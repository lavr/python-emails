# encoding: utf-8
from __future__ import annotations

from .packages.dkim import DKIMException


class HTTPLoaderError(Exception):
    pass


class BadHeaderError(ValueError):
    pass


class IncompleteMessage(ValueError):
    pass