# encoding: utf-8
from __future__ import unicode_literals

__all__ = [ 'SMTPSender' ]

import smtplib
import logging
import threading

from .smtp import SMTPResponse, ResponsibleSMTP, ResponsibleSMTP_SSL
from emails.compat import urlparse, to_native, string_types, to_unicode, to_bytes, text_type
from emails.utils import sanitize_address


class SMTPBackend:

    """
    SMTPSender is a wrapper for smtplib.SMTP class.
    Differences are:
    a) it transparently uses SSL or no-SSL connection
    b) sendmail method sends only one message, but returns more information
       about server response (i.e. response code)
    """

    MAX_SENDMAIL_RETRY = 2
    DEFAULT_SOCKET_TIMEOUT = 5

    connection_cls = ResponsibleSMTP
    connection_ssl_cls = ResponsibleSMTP_SSL


    def __init__(self,
                 user=None,
                 password=None,
                 ssl=False,
                 tls=False,
                 debug=False,
                 fail_silently=True,
                 **kwargs):

        self.smtp_cls = ssl and self.connection_ssl_cls or self.connection_cls
        self.debug = debug
        self.ssl = ssl
        self.tls = tls
        if self.ssl and self.tls:
            raise ValueError(
                "ssl/tls are mutually exclusive, so only set "
                "one of those settings to True.")

        self.user = user
        self.password = password
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.DEFAULT_SOCKET_TIMEOUT
        self.smtp_cls_kwargs = kwargs

        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.fail_silently = fail_silently
        self.connection = None
        #self.local_hostname=DNS_NAME.get_fqdn()
        self._lock = threading.RLock()

    def open(self):
        #logging.debug('SMTPSender _connect')
        if self.connection is None:
            self.connection = self.smtp_cls(**self.smtp_cls_kwargs)
            if self.debug:
                self.connection.set_debuglevel(1)
            if self.tls:
                self.connection.ehlo()
                self.connection.starttls()
                self.connection.ehlo()
            if self.user:
                self.connection.login(user=self.user, password=self.password)
        return self.connection

    def close(self):
        """Closes the connection to the email server."""
        if self.connection is None:
            return
        try:
            try:
                self.connection.quit()
            except (ssl.SSLError, smtplib.SMTPServerDisconnected):
                # This happens when calling quit() on a TLS connection
                # sometimes, or when the connection was already disconnected
                # by the server.
                self.connection.close()
            except:
                if self.fail_silently:
                    return
                raise
        finally:
            self.connection = None


    def make_response(self, error=None):
        r = SMTPResponse(host=self.host, port=self.port)
        if error:
            r.error = error
        return r


    def sendmail(self, **kwargs):

        response = None

        try:
            n = 0
            while n<self.MAX_SENDMAIL_RETRY:
                n += 1
                try:
                    smtpclient = self.open()
                    response = smtpclient._sendmail(**kwargs)
                    response.error = None
                    break
                except smtplib.SMTPServerDisconnected as e:
                    # If server disconected, just connect again
                    logging.exception('Error connecting smtp, step %s of %s', n+1, self.MAX_SENDMAIL_RETRY)
                    self.connection = None
                    if response is None:
                        response = self.make_response(error = e)
                    else:
                        response.error = e
                    continue

        except (IOError, smtplib.SMTPException) as e:
            logging.exception("Error sending mail")
            if response is None:
                response = self.make_response(error = e)
            else:
                response.error = e

        if response.error and not self.fail_silently:
                raise response.error

        return response
