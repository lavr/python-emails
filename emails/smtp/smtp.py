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
        #self.complete = False
        self.success = None
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


    def sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[], to_addr=None):

        # Send one email and returns one response
        if to_addrs:
            if isinstance(to_addrs, (list, tuple)):
                log.warning('Beware: emails.smtp.ResponsibleSMTP.sendmail sends only one message at a time'\
                            'got: to_addrs=%s', to_addrs)
                if len(to_addrs)>1:
                    raise RuntimeError('Can send only one email at a time')
            if to_addr:
                raise RuntimeError('Use "to_addr" or "to_addrs", not both')
            to_addr = to_addrs[0]

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
            exc = smtplib.SMTPRecipientsRefused()
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
