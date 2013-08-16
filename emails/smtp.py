# encoding: utf-8

__all__ = [ 'SMTPConnectionPool', 'SMTPResponse', 'SMTPSender' ]

import smtplib
import logging

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
        return u"<emails.smtp.SMTPResponse status_code=%s status_text=%s>" % (self.status_code.__repr__(),
                                                                              self.status_text.__repr__())


class SMTPSender:

    """
    SMTPSender is a wrapper for smtplib.SMTP class.
    Differences are:
    a) it transparently uses SSL or no-SSL connection
    b) sendmail method sends only one message, but returns more information
       about session (response code, session log, etc)
    """

    MAX_SENDMAIL_RETRY = 2
    DEFAULT_SOCKET_TIMEOUT = 5

    def __init__(self, user=None, password=None, ssl=False, debug=False, raise_on_errors=False, **kwargs):
        self.smtp_cls = ssl and smtplib.SMTP_SSL or smtplib.SMTP
        self.debug = debug
        self.ssl = ssl
        self.user = user
        self.password = password
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.DEFAULT_SOCKET_TIMEOUT
        self.smtp_cls_kwargs = kwargs

        self.smtpclient = None
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.raise_on_errors = raise_on_errors
        self.smtpclient = None

    def _connect(self):
        #logging.debug('SMTPSender _connect')
        if self.smtpclient is None:
            self.smtpclient = self.smtp_cls(**self.smtp_cls_kwargs)
            if self.debug:
                self.smtpclient.set_debuglevel(1)
            if self.user:
                self.smtpclient.login(user=self.user, password=self.password)
        return self.smtpclient

    def _sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):

        if not isinstance(to_addrs, basestring):
            raise NotImplemented('SMTPSender.sendmail can send email to one address only, got to_addrs=%s', to_addrs)

        response = self.response
        smtpclient = self.smtpclient
        smtpclient.ehlo_or_helo_if_needed()

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
            raise smtplib.SMTPSenderRefused(code, resp, from_addr)

        response.to_addr = to_addrs
        response.rcpt_options = rcpt_options

        (code, resp) = smtpclient.rcpt(to_addrs, rcpt_options)
        response.set_status('rcpt', code, resp)

        if (code != 250) and (code != 251):
            smtpclient.rset()
            raise smtplib.SMTPRecipientsRefused()

        (code, resp) = smtpclient.data(msg)
        response.set_status('data', code, resp)
        if code != 250:
            smtpclient.rset()
            raise smtplib.SMTPDataError(code, resp)

        response.success = True
        return response


    def sendmail(self, **kwargs):

        self.response = SMTPResponse(host=self.host, port=self.port, ssl=self.ssl)

        try:

            n = 0
            while n<self.MAX_SENDMAIL_RETRY:
                n += 1
                try:
                    smtpclient = self._connect()
                    self._sendmail(**kwargs)
                    self.response.error = None
                    break
                except smtplib.SMTPServerDisconnected as e:
                    # If server disconected, just connect again
                    #logging.exception('Error connecting smtp')
                    self.smtpclient = None
                    self.response.error = e
                    continue

        except (IOError, smtplib.SMTPException) as e:
            self.response.error = e

        if self.response.error and self.raise_on_errors:
                raise self.response.error

        return self.response





def _serialize_dict(d):
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

        kk = _serialize_dict(k)

        r = self.pool.get(kk, None)

        if r is None:
            r = self.smtp_cls(**k)
            self.pool[kk] = r

        return r

    def reconnect(self, k):

        kk = _serialize_dict(k)

        if kk in self.pool:
            del self.pool[kk]

        return self[k]
