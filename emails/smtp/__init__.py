# encoding: utf-8
__author__ = 'lavrinenko'

from .factory import ObjectFactory
from .client import SMTPResponse
from .backend import SMTPBackend

SMTPConnectionFactory = ObjectFactory(cls=SMTPBackend)
