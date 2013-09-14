# encoding: utf-8

__all__ = [ 'SMTPResponse', 'ResponsibleSMTP' ]

from smtplib import _have_ssl, SMTP
import smtplib

from emails.compat import to_unicode, string_types

class SMTPResponse(object):

    def __init__(self, host=None, port=None, ssl=None):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.responses = []
        self.error = None
        self.exception = None
        self.complete = False
        self.from_addr = None
        self.esmtp_opts = None
        self.rcpt_options = None
        self.to_addr = None
        self.status_code = None
        self.status_text = None
        self.last_command = None

    def set_status(self, command, code, text):
        self.responses.append( [command, code, text] )
        self.status_code = code
        self.status_text = text
        self.last_command = command

    def set_exception(self, exc):
        self.exception = exc

    def __repr__(self):
        return "<emails.smtp.SMTPResponse status_code=%s status_text=%s>" % (self.status_code.__repr__(),
                                                                              self.status_text.__repr__())




class ResponsibleSMTP(SMTP):

    response_cls = SMTPResponse

    def make_response(self):
        if self.sock:
            host, port = self.sock.getpeername()
        else:
            host, port = None, None
        return self.response_cls(host=host, port=port)

    def __example_sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):

        if not to_addrs:
            return False

        from_addr = sanitize_address(from_addr, email_message.encoding)
        recipients = [sanitize_address(addr, email_message.encoding)
                      for addr in email_message.recipients()]
        message = email_message.message()
        charset = message.get_charset().get_output_charset() if message.get_charset() else 'utf-8'
        try:
            self.connection.sendmail(from_email, recipients,
                    force_bytes(message.as_string(), charset))
        except:
            if not self.fail_silently:
                raise
            return False
        return True

    def _sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):

        if isinstance(to_addrs, string_types):
            to_addrs = [to_addrs, ]

        if len(to_addrs)>1:
            log.warning('Beware: emails.smtp.SMTPWithResponse sends separate message'
                        'to each recipients (got %d recipients)')


        smtpclient = self
        smtpclient.ehlo_or_helo_if_needed()

        esmtp_opts = []
        if smtpclient.does_esmtp:
            if smtpclient.has_extn('size'):
                esmtp_opts.append("size=%d" % len(msg))
            for option in mail_options:
                esmtp_opts.append(option)

        for to_addr in to_addrs:

            response = self.make_response()

            response.from_addr = from_addr
            response.esmtp_opts = esmtp_opts[:]

            (code, resp) = smtpclient.mail(from_addr, esmtp_opts)
            response.set_status('mail', code, resp)

            if code != 250:
                smtpclient.rset()
                exc = smtplib.SMTPSenderRefused(code, resp, from_addr)
                response.set_exception(exc)
                yield response
                continue

            response.to_addr = to_addr
            response.rcpt_options = rcpt_options[:]

            (code, resp) = smtpclient.rcpt(to_addr, rcpt_options)
            response.set_status('rcpt', code, resp)

            if (code != 250) and (code != 251):
                smtpclient.rset()
                exc = smtplib.SMTPRecipientsRefused()
                response.set_exception(exc)
                yield response
                continue

            (code, resp) = smtpclient.data(msg)
            response.set_status('data', code, resp)
            if code != 250:
                smtpclient.rset()
                exc = smtplib.SMTPDataError(code, resp)
                response.set_exception(exc)
                yield response
                continue

            response.success = True
            yield response


if _have_ssl:

    from smtplib import SMTP_SSL

    class ResponsibleSMTP_SSL(ResponsibleSMTP, SMTP_SSL):
        pass

else:

    class ResponsibleSMTP_SSL:
        def __init__(self, *args, **kwargs):
            # should raise import error here
            import ssl


__all__.append('ResponsibleSMTP_SSL')
