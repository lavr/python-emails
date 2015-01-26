# encoding: utf-8
from __future__ import unicode_literals

__all__ = [ 'SMTPSender' ]

import smtplib
import logging
import threading
from functools import wraps

from .client import SMTPResponse, SMTPClientWithResponse, SMTPClientWithResponse_SSL
from emails.compat import to_bytes

logger = logging.getLogger(__name__)

class SMTPBackend:

    """
    SMTPSender is a wrapper for smtplib.SMTP class.
    Differences are:
    a) it transparently uses SSL or no-SSL connection
    b) sendmail method sends only one message, but returns more information
       about server response (i.e. response code)
    """

    DEFAULT_SOCKET_TIMEOUT = 5

    connection_cls = SMTPClientWithResponse
    connection_ssl_cls = SMTPClientWithResponse_SSL
    response_cls = SMTPResponse


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
        #logger.debug('SMTPSender _connect')
        if self.connection is None:
            self.connection = self.smtp_cls(parent=self, **self.smtp_cls_kwargs)
            self.connection.initialize()
        return self.connection

    def close(self):
        """Closes the connection to the email server."""

        if self.connection is None:
            return

        try:
            self.connection.close()
        except:
                if self.fail_silently:
                    return
                raise
        finally:
            self.connection = None


    def make_response(self, exception=None):
        return self.response_cls(host=self.host, port=self.port, exception=exception)

    def retry_on_disconnect(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except smtplib.SMTPServerDisconnected as e:
                # If server disconected, just connect again
                logging.debug('SMTPServerDisconnected, retry once')
                self.close()
                self.open()
                return func(*args, **kwargs)
        return wrapper

    def _sendmail_on_connection(self, *args, **kwargs):
        return self.connection.sendmail(*args, **kwargs)

    def sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):

        if not to_addrs: return False

        if not isinstance(to_addrs, (list, tuple)):
            to_addrs = [to_addrs, ]

        #from_addr = sanitize_address(from_addr, email_message.encoding)
        #to_addrs = [sanitize_address(addr, email_message.encoding) for addr in to_addrs]
        #message = email_message.message()
        #charset = message.get_charset().get_output_charset() if message.get_charset() else 'utf-8'

        try:
            self.open()
        except (IOError, smtplib.SMTPException) as e:
            logger.exception("Error connecting smtp server")
            response = self.make_response(exception = e)
            if not self.fail_silently:
                response.raise_if_needed()
            return [response, ]

        _sendmail = self.retry_on_disconnect(self._sendmail_on_connection)

        response = _sendmail(from_addr=from_addr,
                             to_addrs=to_addrs,
                             msg=to_bytes(msg.as_string(), 'utf-8'),
                             mail_options=mail_options,
                             rcpt_options=rcpt_options)

        if not self.fail_silently:
            [ r.raise_if_needed() for r in response ]

        return response

