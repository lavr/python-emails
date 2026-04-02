from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiosmtplib

from ..response import SMTPResponse
from .aio_client import AsyncSMTPClientWithResponse
from ...utils import DNS_NAME
from .exceptions import SMTPConnectNetworkError


__all__ = ['AsyncSMTPBackend']

logger = logging.getLogger(__name__)


class AsyncSMTPBackend:

    """
    AsyncSMTPBackend manages an async SMTP connection using aiosmtplib.
    """

    DEFAULT_SOCKET_TIMEOUT = 5

    response_cls = SMTPResponse

    def __init__(self, ssl: bool = False, fail_silently: bool = True,
                 mail_options: list[str] | None = None, **kwargs: Any) -> None:

        self.ssl = ssl
        self.tls = kwargs.get('tls')
        if self.ssl and self.tls:
            raise ValueError(
                "ssl/tls are mutually exclusive, so only set "
                "one of those settings to True.")

        kwargs.setdefault('timeout', self.DEFAULT_SOCKET_TIMEOUT)
        kwargs.setdefault('local_hostname', DNS_NAME.get_fqdn())
        kwargs['port'] = int(kwargs.get('port', 0))

        self.smtp_cls_kwargs = kwargs

        self.host: str | None = kwargs.get('host')
        self.port: int = kwargs['port']
        self.fail_silently = fail_silently
        self.mail_options = mail_options or []

        self._client: AsyncSMTPClientWithResponse | None = None
        self._lock = asyncio.Lock()

    async def get_client(self) -> AsyncSMTPClientWithResponse:
        async with self._lock:
            return await self._get_client_unlocked()

    async def _get_client_unlocked(self) -> AsyncSMTPClientWithResponse:
        if self._client is None:
            client = AsyncSMTPClientWithResponse(
                parent=self, ssl=self.ssl, **self.smtp_cls_kwargs
            )
            await client.initialize()
            self._client = client
        return self._client

    async def close(self) -> None:
        """Closes the connection to the email server."""
        async with self._lock:
            await self._close_unlocked()

    async def _close_unlocked(self) -> None:
        if self._client:
            try:
                await self._client.quit()
            except Exception:
                if self.fail_silently:
                    return
                raise
            finally:
                self._client = None

    def make_response(self, exception: Exception | None = None) -> SMTPResponse:
        return self.response_cls(backend=self, exception=exception)

    async def _send(self, **kwargs: Any) -> SMTPResponse | None:
        response = None
        try:
            client = await self._get_client_unlocked()
        except aiosmtplib.SMTPConnectError as exc:
            cause = exc.__cause__
            if isinstance(cause, IOError):
                response = self.make_response(
                    exception=SMTPConnectNetworkError.from_ioerror(cause))
            else:
                response = self.make_response(exception=exc)
            if not self.fail_silently:
                raise
        except aiosmtplib.SMTPException as exc:
            response = self.make_response(exception=exc)
            if not self.fail_silently:
                raise
        except IOError as exc:
            response = self.make_response(
                exception=SMTPConnectNetworkError.from_ioerror(exc))
            if not self.fail_silently:
                raise

        if response:
            return response
        else:
            return await client.sendmail(**kwargs)

    async def _send_with_retry(self, **kwargs: Any) -> SMTPResponse | None:
        async with self._lock:
            try:
                return await self._send(**kwargs)
            except aiosmtplib.SMTPServerDisconnected:
                logger.debug('SMTPServerDisconnected, retry once')
                await self._close_unlocked()
                return await self._send(**kwargs)

    async def sendmail(self, from_addr: str, to_addrs: str | list[str],
                       msg: Any, mail_options: list[str] | None = None,
                       rcpt_options: list[str] | None = None) -> SMTPResponse | None:

        if not to_addrs:
            return None

        if not isinstance(to_addrs, (list, tuple)):
            to_addrs = [to_addrs]

        response = await self._send_with_retry(
            from_addr=from_addr,
            to_addrs=to_addrs,
            msg=msg.as_bytes(),
            mail_options=mail_options or self.mail_options,
            rcpt_options=rcpt_options,
        )

        if response and not self.fail_silently:
            response.raise_if_needed()

        return response

    async def __aenter__(self) -> AsyncSMTPBackend:
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None,
                        exc_value: BaseException | None,
                        traceback: Any | None) -> None:
        await self.close()
