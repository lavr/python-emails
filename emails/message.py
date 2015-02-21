# coding: utf-8
from __future__ import unicode_literals

import time
from functools import wraps

from dateutil.parser import parse as dateutil_parse
from email.header import Header
from email.utils import formatdate, getaddresses

from emails.compat import string_types, to_unicode, is_callable, to_bytes

from .utils import SafeMIMEText, SafeMIMEMultipart, sanitize_address, parse_name_and_email
from .smtp import ObjectFactory, SMTPBackend
from .store import MemoryFileStore, BaseFile
from .signers import DKIMSigner

from .utils import load_email_charsets

load_email_charsets()  # sic!

ROOT_PREAMBLE = 'This is a multi-part message in MIME format.\n'


class BadHeaderError(ValueError):
    pass

# Header names that contain structured address data (RFC #5322)
ADDRESS_HEADERS = set(['from', 'sender', 'reply-to', 'to', 'cc', 'bcc', 'resent-from', 'resent-sender', 'resent-to',
                   'resent-cc', 'resent-bcc'])


def renderable(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        r = f(self, *args, **kwargs)
        render = getattr(r, 'render', None)
        if render:
            d = render(**(self.render_data or {}))
            return d
        else:
            return r

    return wrapper


class IncompleteMessage(Exception):
    pass


class Message(object):
    """
    Email class

        message = HtmlEmail()

    Message parts:
        * html
        * text
        * attachments

    """

    attachment_cls = BaseFile
    dkim_cls = DKIMSigner
    smtp_pool_factory = ObjectFactory
    smtp_cls = SMTPBackend
    filestore_cls = MemoryFileStore

    def __init__(self,
                 charset=None,
                 message_id=None,
                 date=None,
                 subject=None,
                 mail_from=None,
                 mail_to=None,
                 headers=None,
                 html=None,
                 text=None,
                 attachments=None):

        self._attachments = None
        self.charset = charset or 'utf-8'  # utf-8 is standard de-facto, yeah
        self._message_id = message_id
        self.set_subject(subject)
        self.set_date(date)
        self.set_mail_from(mail_from)
        self.set_mail_to(mail_to)
        self.set_headers(headers)
        self.set_html(html=html)  # , url=self.html_from_url)
        self.set_text(text=text)  # , url=self.text_from_url)
        self.render_data = {}
        self._dkim_signer = None
        if attachments:
            for a in attachments:
                self.attachments.add(a)

        self.after_build = None

    def set_mail_from(self, mail_from):
        # In: ('Alice', '<alice@me.com>' )
        self._mail_from = mail_from and parse_name_and_email(mail_from) or None

    def set_mail_to(self, mail_to):
        # Now we parse only one to-addr
        # TODO: parse list of to-addrs
        mail_to = mail_to and parse_name_and_email(mail_to)
        self._mail_to = mail_to and [mail_to, ] or []

    def get_mail_to(self):
        return self._mail_to

    mail_to = property(get_mail_to, set_mail_to)

    def set_headers(self, headers):
        self._headers = headers

    def set_html(self, html, url=None):
        if hasattr(html, 'read'):
            html = html.read()
        self._html = html
        self._html_url = url

    def set_text(self, text, url=None):
        if hasattr(text, 'read'):
            text = text.read()
        self._text = text
        self._text_url = url

    def attach(self, **kwargs):
        if 'content_disposition' not in kwargs:
            kwargs['content_disposition'] = 'attachment'
        self.attachments.add(kwargs)

    @classmethod
    def from_loader(cls, loader, template_cls=None, **kwargs):
        """
        Get html and attachments from Loader
        """

        html = loader.html
        if html and template_cls:
            html = template_cls(html)

        text = loader.text
        if text and template_cls:
            text = template_cls(text)

        message = cls(html=html, text=text, **kwargs)

        for attachment in loader.attachments:
            message.attach(**attachment)
        return message

    @property
    @renderable
    def html_body(self):
        return self._html

    @property
    @renderable
    def text_body(self):
        return self._text

    def set_subject(self, value):
        self._subject = value

    @renderable
    def get_subject(self):
        return self._subject

    subject = property(get_subject, set_subject)

    def render(self, **kwargs):
        self.render_data = kwargs

    @property
    def attachments(self):
        if self._attachments is None:
            self._attachments = self.filestore_cls(self.attachment_cls)
        return self._attachments

    def set_date(self, value):
        if isinstance(value, string_types):
            _d = dateutil_parse(value)
            value = time.mktime(_d.timetuple())
            value = formatdate(value, True)
        self._date = value

    def get_date(self):
        if self._date is False:
            return None
        timeval = self._date
        if timeval:
            if is_callable(timeval):
                timeval = timeval()
        elif timeval is None:
            timeval = formatdate(None, True)
        return timeval

    message_date = property(get_date, set_date)

    def message_id(self):
        mid = self._message_id
        if mid is False:
            return None
        return is_callable(mid) and mid() or mid

    def encode_header(self, value):
        value = to_unicode(value, charset=self.charset)
        if isinstance(value, string_types):
            value = value.rstrip()
            _r = Header(value, self.charset)
            return str(_r)
        else:
            return value

    def encode_name_header(self, realname, email):
        if realname:
            r = "%s <%s>" % (self.encode_header(realname), email)
            return r
        else:
            return email

    def set_header(self, msg, key, value, encode=True):

        if value is None:
            # TODO: may be remove header here ?
            return

        # Prevent header injection
        if '\n' in value or '\r' in value:
            raise BadHeaderError("Header values can't contain newlines (got %r for header %r)" % (value, key))

        if key.lower() in ADDRESS_HEADERS:
            value = ', '.join(sanitize_address(addr, self.charset)
                              for addr in getaddresses((value,)))

        msg[key] = encode and self.encode_header(value) or value

    def _build_message(self, message_cls=None):

        message_cls = message_cls or SafeMIMEMultipart
        msg = message_cls()

        msg.preamble = ROOT_PREAMBLE

        self.set_header(msg, 'Date', self.message_date, encode=False)
        self.set_header(msg, 'Message-ID', self.message_id(), encode=False)

        if self._headers:
            for (name, value) in self._headers.items():
                self.set_header(msg, name, value)

        subject = self.subject
        if subject is None:
            raise IncompleteMessage("Message must have 'subject'")
        self.set_header(msg, 'Subject', subject)

        mail_from = self.encode_name_header(*self._mail_from)
        # if mail_from is None:
        #    raise IncompleteMessage("Message must have 'mail_from'")
        self.set_header(msg, 'From', mail_from, encode=False)

        mail_to = self._mail_to and self.encode_name_header(*self._mail_to[0]) or None
        self.set_header(msg, 'To', mail_to, encode=False)

        msgalt = SafeMIMEMultipart('alternative')
        msg.attach(msgalt)

        _text = self.text_body
        _html = self.html_body

        if not (_html or _text):
            raise ValueError("Message must contain 'html' or 'text' part")

        if _text:
            msgtext = SafeMIMEText(_text, 'plain', charset=self.charset)
            msgtext.set_charset(self.charset)
            msgalt.attach(msgtext)

        if _html:
            msghtml = SafeMIMEText(_html, 'html', charset=self.charset)
            msghtml.set_charset(self.charset)
            msgalt.attach(msghtml)

        for f in self.attachments:
            msgfile = f.mime
            if msgfile:
                msg.attach(msgfile)

        if self.after_build:
            self.after_build(self, msg)

        return msg

    def message(self, message_cls=None):
        msg = self._build_message(message_cls=message_cls)
        if self._dkim_signer:
            msg_str = msg.as_string()
            dkim_header = self._dkim_signer.get_sign_header(to_bytes(msg_str))
            if dkim_header:
                msg._headers.insert(0, dkim_header)
        return msg

    def as_string(self):
        # self.as_string() is not equialent self.message().as_string()
        # self.as_string() gets one less message-to-string conversions for dkim
        msg = self._build_message()
        r = msg.as_string()
        if self._dkim_signer:
            dkim_header = self._dkim_signer.get_sign(to_bytes(r))
            if dkim_header:
                r = dkim_header + r
        return r

    @property
    def smtp_pool(self):
        pool = getattr(self, '_smtp_pool', None)
        if pool is None:
            pool = self._smtp_pool = self.smtp_pool_factory(cls=self.smtp_cls)
        return pool

    def dkim(self, **kwargs):
        self._dkim_signer = self.dkim_cls(**kwargs)

    def send(self,
             to=None,
             set_mail_to=True,
             mail_from=None,
             set_mail_from=False,
             render=None,
             smtp_mail_options=None,
             smtp_rcpt_options=None,
             smtp=None):

        if render is not None:
            self.render(**render)

        if smtp is None:
            smtp = {'host': 'localhost', 'port': 25, 'timeout': 5}

        if isinstance(smtp, dict):
            smtp = self.smtp_pool[smtp]

        if not hasattr(smtp, 'sendmail'):
            raise ValueError(
                "smtp must be a dict or an object with method 'sendmail'. got %s" % type(smtp))

        mail_to = to
        if mail_to:
            mail_to = parse_name_and_email(mail_to)
            to_addr = mail_to[1]
            if set_mail_to:
                self.set_mail_to(mail_to)

        else:
            to_addr = self._mail_to[0][1]

        if not to_addr:
            raise ValueError('No to-addr')

        if mail_from:
            if set_mail_from:
                self.set_mail_from(mail_from)
                from_addr = self._mail_from[1]
            else:
                mail_from = parse_name_and_email(mail_from)
                from_addr = mail_from[1]
        else:
            from_addr = self._mail_from[1]

        if not from_addr:
            raise ValueError('No from-addr')

        params = dict(from_addr=from_addr,
                      to_addrs=[to_addr, ],
                      msg=self)
        if smtp_mail_options:
            params['mail_options'] = smtp_mail_options

        if smtp_rcpt_options:
            params['rcpt_options'] = smtp_rcpt_options

        response = smtp.sendmail(**params)
        return response[0]


def html(**kwargs):
    return Message(**kwargs)

