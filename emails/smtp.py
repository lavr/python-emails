# encoding: utf-8

__all__ = [ 'SMTPConnectionPool', 'SMTPResponse', 'SMTPSender' ]

import smtplib

class SMTPResponse(object):

    def __init__(self, host=None, port=None, ssl=None):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.responses = []
        self.error = None
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

    def __repr__(self):
        return u"<emails.smtp.SMTPResponse status_code=%s status_text=%s>" % (self.status_code, self.status_text)


class SMTPSender:

    """
    SMTPSender is a wrapper for smtplib.SMTP class.
    Differences are:
    a) it transparently uses SSL or no-SSL connection
    b) sendmail method sends only one message, but returns more information
       about session (response code, session log, etc)
    """

    def __init__(self, user=None, password=None, ssl=False, debug=False, **kwargs):
        self.smtp_cls = ssl and smtplib.SMTP_SSL or smtplib.SMTP
        self.debug = debug
        self.ssl = ssl
        self.user = user
        self.password = password
        self.smtp_cls_kwargs = kwargs
        self.smtpclient = None
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.start_connection()

    #def __getattr__(self, k):
    #    return getattr(self.smtpclient, k)

    def start_connection(self):
        self.smtpclient = self.smtp_cls(**self.smtp_cls_kwargs)

        if self.debug:
            self.smtpclient.set_debuglevel(1)
        if self.user:
            self.smtpclient.login(user=self.user, password=self.password)

    def sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):

        if not isinstance(to_addrs, basestring):
            raise NotImplemented('SMTPSender.sendmail can send email to one address only, got to_addrs=%s', to_addrs)

        smtpclient = self.smtpclient

        smtpclient.ehlo_or_helo_if_needed()


        response = SMTPResponse(host = self.host, port=self.port, ssl=self.ssl)

        esmtp_opts = []
        if smtpclient.does_esmtp:
            if smtpclient.has_extn('size'):
                esmtp_opts.append("size=%d" % len(msg))
            for option in mail_options:
                esmtp_opts.append(option)

        response.from_addr = from_addr
        response.esmtp_opts = esmtp_opts

        (code, resp) = smtpclient.mail(from_addr, esmtp_opts)
        response.set_status('mail', code, resp)

        if code != 250:
            smtpclient.rset()
            response.error = smtplib.SMTPSenderRefused(code, resp, from_addr)
            return response

        response.to_addr = to_addrs
        response.rcpt_options = rcpt_options

        (code, resp) = smtpclient.rcpt(to_addrs, rcpt_options)
        response.set_status('rcpt', code, resp)

        if (code != 250) and (code != 251):
            smtpclient.rset()
            response.error = smtplib.SMTPRecipientsRefused(senderrs)
            return response

        (code, resp) = smtpclient.data(msg)
        response.set_status('data', code, resp)
        if code != 250:
            smtpclient.rset()
            response.error = smtplib.SMTPDataError(code, resp)
            return response

        response.success = True
        return response



def serialize_dict(d):
    # simple dict serializer
    r = []
    for (k, v) in d.iteritems():
        r.append("%s=%s" % (k, v))
    return ";".join(r)


class SMTPConnectionPool:

    smtp_cls = SMTPSender

    def __init__(self):
        self.pool = {}

    def __getitem__(self, k):

        if not isinstance(k, dict):
            raise ValueError("item must be dict, not %s" % type(k))

        kk = serialize_dict(k)

        r = self.pool.get(kk, None)

        if r is None:
            r = self.smtp_cls(**k)
            self.pool[kk] = r

        return r

    def reconnect(self, k):

        kk = serialize_dict(k)

        if kk in self.pool:
            del self.pool[kk]

        return self[k]
