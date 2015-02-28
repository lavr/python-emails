# encoding: utf-8
__all__ = ['SMTPResponse', 'SMTPClientWithResponse', 'SMTPClientWithResponse_SSL']

from smtplib import _have_ssl, SMTP
import smtplib
import logging

logger = logging.getLogger(__name__)

class SMTPResponse(object):

    def __init__(self, host=None, port=None, ssl=None, exception=None):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.responses = []
        self.exception = exception
        self.success = None
        self.from_addr = None
        self.esmtp_opts = None
        self.rcpt_options = None
        self.to_addr = None
        self.status_code = None
        self.status_text = None
        self.last_command = None

    def set_status(self, command, code, text):
        self.responses.append([command, code, text])
        self.status_code = code
        self.status_text = text
        self.last_command = command

    def set_exception(self, exc):
        self.exception = exc

    def raise_if_needed(self):
        if self.exception:
            raise self.exception

    @property
    def error(self):
        return self.exception

    def __repr__(self):
        return "<emails.smtp.SMTPResponse status_code=%s status_text=%s>" % (self.status_code.__repr__(),
                                                                              self.status_text.__repr__())


class SMTPClientWithResponse(SMTP):

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.make_response = parent.make_response
        self._last_smtp_response = (None, None)
        self.tls = kwargs.pop('tls', False)
        self.ssl = kwargs.pop('ssl', False)
        self.debug = kwargs.pop('debug', 0)
        self.set_debuglevel(self.debug)
        self.user = kwargs.pop('user', None)
        self.password = kwargs.pop('password', None)
        SMTP.__init__(self, **kwargs)
        self.initialize()

    def initialize(self):
        if self.tls:
            self.starttls()
        if self.user:
            self.login(user=self.user, password=self.password)
        self.ehlo_or_helo_if_needed()
        return self

    def quit(self):
        """Closes the connection to the email server."""
        try:
            SMTP.quit(self)
        except (smtplib.SMTPServerDisconnected, ):
            # This happens when calling quit() on a TLS connection
            # sometimes, or when the connection was already disconnected
            # by the server.
            self.close()

    def data(self, msg):
        (code, msg) = SMTP.data(self, msg)
        self._last_smtp_response = (code, msg)
        return code, msg

    def _send_one_mail(self, from_addr, to_addr, msg, mail_options=[], rcpt_options=[]):

        esmtp_opts = []
        if self.does_esmtp:
            if self.has_extn('size'):
                esmtp_opts.append("size=%d" % len(msg))
            for option in mail_options:
                esmtp_opts.append(option)

        response = self.make_response()

        response.from_addr = from_addr
        response.esmtp_opts = esmtp_opts[:]

        (code, resp) = self.mail(from_addr, esmtp_opts)
        response.set_status('mail', code, resp)

        if code != 250:
            self.rset()
            exc = smtplib.SMTPSenderRefused(code, resp, from_addr)
            response.set_exception(exc)
            return response

        response.to_addr = to_addr
        response.rcpt_options = rcpt_options[:]

        (code, resp) = self.rcpt(to_addr, rcpt_options)
        response.set_status('rcpt', code, resp)

        if (code != 250) and (code != 251):
            self.rset()
            exc = smtplib.SMTPRecipientsRefused(to_addr)
            response.set_exception(exc)
            return response

        (code, resp) = self.data(msg)
        response.set_status('data', code, resp)
        if code != 250:
            self.rset()
            exc = smtplib.SMTPDataError(code, resp)
            response.set_exception(exc)
            return response

        response.success = True
        return response

    def sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):
        # Send one email and returns one response
        if not to_addrs:
            return []

        assert isinstance(to_addrs, (list, tuple))

        if len(to_addrs)>1:
            logger.warning('Beware: emails.smtp.client.SMTPClientWithResponse.sendmail sends full message to each email')

        return [self._send_one_mail(from_addr, to_addr, msg, mail_options, rcpt_options) \
                        for to_addr in to_addrs]



if _have_ssl:

    from smtplib import SMTP_SSL
    import ssl

    class SMTPClientWithResponse_SSL(SMTP_SSL, SMTPClientWithResponse):

        def __init__(self, **kw):
            args = {}
            for k in ('host', 'port', 'local_hostname', 'keyfile', 'certfile', 'timeout'):
                if k in kw:
                    args[k] = kw[k]
            SMTP_SSL.__init__(self, **args)
            SMTPClientWithResponse.__init__(self, **kw)

        def data(self, msg):
            (code, msg) = SMTP.data(self, msg)
            self._last_smtp_response = (code, msg)
            return code, msg

        def quit(self):
            """Closes the connection to the email server."""
            try:
                SMTPClientWithResponse.quit(self)
            except (ssl.SSLError, smtplib.SMTPServerDisconnected):
                # This happens when calling quit() on a TLS connection
                # sometimes, or when the connection was already disconnected
                # by the server.
                self.close()

        def sendmail(self, *args, **kw):
            return SMTPClientWithResponse.sendmail(self, *args, **kw)

else:

    class SMTPClientWithResponse_SSL:
        def __init__(self, *args, **kwargs):
            # should raise import error here
            import ssl



