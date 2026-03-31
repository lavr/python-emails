# encoding: utf-8
# This module use pydkim for DKIM signature
from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from typing import IO

from .packages import dkim
from .packages.dkim import DKIMException, UnparsableKeyError
from .packages.dkim.crypto import parse_pem_private_key
from .utils import to_bytes, to_native


class DKIMSigner:

    def __init__(self, selector: str, domain: str, key: str | bytes | IO[bytes] | None = None,
                 ignore_sign_errors: bool = False, **kwargs: object) -> None:

        self.ignore_sign_errors = ignore_sign_errors
        self._sign_params = kwargs

        privkey = key or kwargs.pop('privkey', None)  # privkey is legacy synonym for `key`

        if not privkey:
            raise TypeError("DKIMSigner.__init__() requires 'key' argument")

        if privkey and hasattr(privkey, 'read'):
            privkey = privkey.read()

        # Compile private key
        try:
            privkey = parse_pem_private_key(to_bytes(privkey))  # type: ignore[arg-type]
        except UnparsableKeyError as exc:
            raise DKIMException(exc)

        self._sign_params.update({'privkey': privkey,
                                  'domain': to_bytes(domain),
                                  'selector': to_bytes(selector)})

    def get_sign_string(self, message: bytes) -> bytes | None:
        try:
            # pydkim module parses message and privkey on each signing
            # this is not optimal for mass operations
            # TODO: patch pydkim or use another signing module
            return dkim.sign(message=message, **self._sign_params)  # type: ignore[no-any-return]
        except DKIMException:
            if self.ignore_sign_errors:
                logging.exception('Error signing message')
            else:
                raise
        return None

    def get_sign_bytes(self, message: bytes) -> bytes | None:
        return self.get_sign_string(message)

    def get_sign_header(self, message: bytes) -> tuple[str, str] | None:
        # pydkim returns string, so we should split
        s = self.get_sign_string(message)
        if s:
            (header, value) = to_native(s).split(': ', 1)  # type: ignore[union-attr]
            if value.endswith("\r\n"):
                value = value[:-2]
            return header, value
        return None

    def sign_message(self, msg: MIMEMultipart) -> MIMEMultipart:
        """
        Add DKIM header to email.message
        """

        # py3 pydkim requires bytes to compute dkim header
        # but py3 smtplib requires str to send DATA command (#
        # so we have to convert msg.as_string

        dkim_header = self.get_sign_header(to_bytes(msg.as_string()))  # type: ignore[arg-type]
        if dkim_header:
            msg._headers.insert(0, dkim_header)  # type: ignore[attr-defined]
        return msg

    def sign_message_string(self, message_string: str) -> str:
        """
        Insert DKIM header to message string
        """

        # py3 pydkim requires bytes to compute dkim header
        # but py3 smtplib requires str to send DATA command
        # so we have to convert message_string

        s = self.get_sign_string(to_bytes(message_string))  # type: ignore[arg-type]
        return s and to_native(s) + message_string or message_string  # type: ignore[operator]

    def sign_message_bytes(self, message_bytes: bytes) -> bytes:
        """
        Insert DKIM header to message bytes
        """
        s = self.get_sign_bytes(message_bytes)
        return s and to_bytes(s) + message_bytes or message_bytes  # type: ignore[operator]
