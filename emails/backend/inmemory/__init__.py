# encoding: utf-8
from __future__ import unicode_literals

__all__ = ['InMemoryBackend', ]

import logging


class InMemoryBackend(object):

    """
    InMemoryBackend store message in memory for testing purposes.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.messages = {}

    def sendmail(self, from_addr, to_addrs, msg, **kwargs):

        logging.debug('InMemoryBackend.sendmail(%s, %s, %r, %s)', from_addr, to_addrs, msg, kwargs)

        if not to_addrs:
            return None

        if not isinstance(to_addrs, (list, tuple)):
            to_addrs = [to_addrs, ]

        for addr in to_addrs:
            data = dict(from_addr=from_addr,
                        message=msg.as_string(),
                        source_message=msg,
                        **kwargs)
            self.messages.setdefault(addr.lower(), []).append(data)

        return True
