# coding: utf-8
from __future__ import unicode_literals
from time import mktime
from email.utils import getaddresses

from dateutil.parser import parse as dateutil_parse

from .compat import (string_types, is_callable, to_bytes)
from .utils import (SafeMIMEText, SafeMIMEMultipart, sanitize_address,
                    parse_name_and_email, load_email_charsets,
                    encode_header as encode_header_,
                    renderable, format_date_header)
from .exc import BadHeaderError
from .backend import ObjectFactory, SMTPBackend
from .store import MemoryFileStore, BaseFile
from .signers import DKIMSigner


load_email_charsets()  # sic!


class BaseMessage(object):

    """
    Base email message with html part, text part and attachments.
    """

    attachment_cls = BaseFile
    filestore_cls = MemoryFileStore
    policy = None

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
        self.set_html(html=html)
        self.set_text(text=text)
        self.render_data = {}

        if attachments:
            for a in attachments:
                self.attachments.add(a)

    def set_mail_from(self, mail_from):
        # In: ('Alice', '<alice@me.com>' )
        self._mail_from = mail_from and parse_name_and_email(mail_from) or None

    def get_mail_from(self):
        # Out: ('Alice', '<alice@me.com>') or None
        return self._mail_from

    mail_from = property(get_mail_from, set_mail_from)

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

    def get_html(self):
        return self._html

    html = property(get_html, set_html)

    def set_text(self, text, url=None):
        if hasattr(text, 'read'):
            text = text.read()
        self._text = text
        self._text_url = url

    def get_text(self):
        return self._text

    text = property(get_text, set_text)

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

    def set_date(self, value):
        self._date = value

    def get_date(self):
        v = self._date
        if v is False:
            return None
        if is_callable(v):
            v = v()
        if not isinstance(v, string_types):
            v = format_date_header(v)
        return v

    date = property(get_date, set_date)
    message_date = date

    def message_id(self):
        mid = self._message_id
        if mid is False:
            return None
        return is_callable(mid) and mid() or mid

    @property
    def attachments(self):
        if self._attachments is None:
            self._attachments = self.filestore_cls(self.attachment_cls)
        return self._attachments

    def attach(self, **kwargs):
        if 'content_disposition' not in kwargs:
            kwargs['content_disposition'] = 'attachment'
        self.attachments.add(kwargs)


class MessageBuildMixin(object):

    ROOT_PREAMBLE = 'This is a multi-part message in MIME format.\n'

    # Header names that contain structured address data (RFC #5322)
    ADDRESS_HEADERS = set(['from', 'sender', 'reply-to', 'to', 'cc', 'bcc',
                           'resent-from', 'resent-sender', 'resent-to',
                           'resent-cc', 'resent-bcc'])

    before_build = None
    after_build = None

    def encode_header(self, value):
        return encode_header_(value, self.charset)

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

        if key.lower() in self.ADDRESS_HEADERS:
            value = ', '.join(sanitize_address(addr, self.charset)
                              for addr in getaddresses((value,)))

        msg[key] = encode and self.encode_header(value) or value

    def _build_root_message(self, message_cls=None, **kw):

        msg = (message_cls or SafeMIMEMultipart)(**kw)

        if self.policy:
            msg.policy = self.policy

        msg.preamble = self.ROOT_PREAMBLE
        self.set_header(msg, 'Date', self.date, encode=False)
        self.set_header(msg, 'Message-ID', self.message_id(), encode=False)

        if self._headers:
            for (name, value) in self._headers.items():
                self.set_header(msg, name, value)

        subject = self.subject
        if subject is not None:
            self.set_header(msg, 'Subject', subject)

        mail_from = self._mail_from and self.encode_name_header(*self._mail_from) or None
        self.set_header(msg, 'From', mail_from, encode=False)

        mail_to = self._mail_to and self.encode_name_header(*self._mail_to[0]) or None
        self.set_header(msg, 'To', mail_to, encode=False)

        return msg

    def _build_html_part(self):
        text = self.html_body
        if text:
            p = SafeMIMEText(text, 'html', charset=self.charset)
            p.set_charset(self.charset)
            return p

    def _build_text_part(self):
        text = self.text_body
        if text:
            p = SafeMIMEText(text, 'plain', charset=self.charset)
            p.set_charset(self.charset)
            return p

    def build_message(self, message_cls=None):

        if self.before_build:
            self.before_build(self)

        msg = self._build_root_message(message_cls)

        rel = SafeMIMEMultipart('related')
        msg.attach(rel)

        alt = SafeMIMEMultipart('alternative')
        rel.attach(alt)

        _text = self._build_text_part()
        _html = self._build_html_part()

        if not (_html or _text):
            raise ValueError("Message must contain 'html' or 'text'")

        if _text:
            alt.attach(_text)

        if _html:
            alt.attach(_html)

        for f in self.attachments:
            part = f.mime
            if part:
                if f.is_inline:
                    rel.attach(part)
                else:
                    msg.attach(part)

        if self.after_build:
            self.after_build(self, msg)

        return msg

    _build_message = build_message


class MessageSendMixin(object):

    smtp_pool_factory = ObjectFactory
    smtp_cls = SMTPBackend

    @property
    def smtp_pool(self):
        pool = getattr(self, '_smtp_pool', None)
        if pool is None:
            pool = self._smtp_pool = self.smtp_pool_factory(cls=self.smtp_cls)
        return pool

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
            raise ValueError('No "from" addr')

        params = dict(from_addr=from_addr,
                      to_addrs=[to_addr, ],
                      msg=self)
        if smtp_mail_options:
            params['mail_options'] = smtp_mail_options

        if smtp_rcpt_options:
            params['rcpt_options'] = smtp_rcpt_options

        response = smtp.sendmail(**params)
        return response[0]


class MessageTransformerMixin(object):

    transformer_cls = None
    _transformer = None

    def create_transformer(self, transformer_cls=None, **kw):
        cls = transformer_cls or self.transformer_cls
        if cls is None:
            from .transformer import MessageTransformer  # avoid cyclic import
            cls = MessageTransformer
        self._transformer = cls(message=self, **kw)

    def destroy_transformer(self):
        self._transformer = None

    @property
    def transformer(self):
        if self._transformer is None:
            self.create_transformer()
        return self._transformer

    def set_html(self, **kw):
        # When html set, remove old transformer
        self.destroy_transformer()
        BaseMessage.set_html(self, **kw)


class MessageDKIMMixin(object):

    dkim_cls = DKIMSigner
    _dkim_signer = None

    def dkim(self, **kwargs):
        self._dkim_signer = self.dkim_cls(**kwargs)

    def dkim_sign_message(self, msg):
        """
        Add DKIM header
        """
        if self._dkim_signer:
            return self._dkim_signer.sign_message(msg)
        return msg

    def dkim_sign_string(self, message_string):
        """
        Add DKIM header
        """
        if self._dkim_signer:
            return self._dkim_signer.sign_message_string(message_string)
        return message_string

    def as_message(self, message_cls=None):
        return self.dkim_sign_message(self.build_message(message_cls=message_cls))

    message = as_message

    def as_string(self, message_cls=None):
        """
        Returns message as string.

        Note: this method costs one less message-to-string conversions
        for dkim in compare to self.as_message().as_string()

        Changes:
        v0.4.2: now returns bytes, not native string
        """

        return self.dkim_sign_string(to_bytes(self.build_message(message_cls=message_cls).as_string()))


class Message(MessageSendMixin, MessageTransformerMixin, MessageDKIMMixin, MessageBuildMixin, BaseMessage):
    """
    Email message with:
    - DKIM signer
    - smtp send
    - Message.transformer object
    """
    pass


def html(**kwargs):
    return Message(**kwargs)


class DjangoMessageProxy(object):

    """
    Class obsoletes with emails.django_.DjangoMessage

    Class looks like django.core.mail.EmailMessage for standard django email backend.

    Example usage:

        message = emails.Message(html='...', subject='...', mail_from='robot@company.ltd')
        connection = django.core.mail.get_connection()

        message.set_mail_to('somebody@somewhere.net')
        connection.send_messages([DjangoMessageProxy(message), ])
    """

    def __init__(self, message, recipients=None, context=None):
        self._message = message
        self._recipients = recipients
        self._context = context and context.copy() or {}

        self.from_email = message.mail_from[1]
        self.encoding = message.charset

    def recipients(self):
        return self._recipients or [r[1] for r in self._message.mail_to]

    def message(self):
        self._message.render(**self._context)
        return self._message.message()
