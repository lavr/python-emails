# This module use pydkim for DKIM signature
from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from typing import IO

from .packages import dkim
from .packages.dkim import DKIMException, UnparsableKeyError
from .packages.dkim.crypto import parse_pem_private_key


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

        # Normalize to bytes before parsing
        privkey_bytes = privkey if isinstance(privkey, bytes) else str(privkey).encode()

        # Compile private key
        try:
            privkey_parsed = parse_pem_private_key(privkey_bytes)
        except UnparsableKeyError as exc:
            raise DKIMException(exc)

        self._sign_params.update({'privkey': privkey_parsed,
                                  'domain': domain.encode(),
                                  'selector': selector.encode()})

    def get_sign_string(self, message: bytes) -> bytes | None:
        try:
            # pydkim module parses message and privkey on each signing
            # this is not optimal for mass operations
            # TODO: patch pydkim or use another signing module
            result: bytes = dkim.sign(message=message, **self._sign_params)
            return result
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
            (header, value) = s.decode().split(': ', 1)
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

        dkim_header = self.get_sign_header(msg.as_string().encode())
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

        s = self.get_sign_string(message_string.encode())
        if s:
            return s.decode() + message_string
        return message_string

    def sign_message_bytes(self, message_bytes: bytes) -> bytes:
        """
        Insert DKIM header to message bytes
        """
        s = self.get_sign_bytes(message_bytes)
        if s:
            return s + message_bytes
        return message_bytes
