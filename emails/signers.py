# This module uses dkimpy for DKIM signature
from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from typing import IO

import dkim
from dkim import DKIMException, UnparsableKeyError


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

        # Normalize to bytes
        privkey_bytes = privkey if isinstance(privkey, bytes) else str(privkey).encode()

        # Validate key early; dkim.sign() re-parses on each call but
        # the PEM parse cost is negligible vs the RSA operation (~0ms vs ~2.5ms).
        try:
            dkim.crypto.parse_pem_private_key(privkey_bytes)
        except UnparsableKeyError as exc:
            raise DKIMException(exc)

        self._sign_params.update({'privkey': privkey_bytes,
                                  'domain': domain.encode(),
                                  'selector': selector.encode()})

    def get_sign_string(self, message: bytes) -> bytes | None:
        try:
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
        dkim_header = self.get_sign_header(msg.as_string().encode())
        if dkim_header:
            msg._headers.insert(0, dkim_header)  # type: ignore[attr-defined]
        return msg

    def sign_message_string(self, message_string: str) -> str:
        """
        Insert DKIM header to message string
        """
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
