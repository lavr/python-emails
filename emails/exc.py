# encoding: utf-8

from emails.packages.dkim import DKIMException

class HTTPLoaderError(Exception):
    pass

class BadHeaderError(ValueError):
    pass
