from __future__ import annotations

__all__ = ["AsyncSMTPClientWithResponse"]

import logging
from typing import TYPE_CHECKING

import aiosmtplib

from ..response import SMTPResponse
from ...utils import sanitize_email

if TYPE_CHECKING:
    from .aio_backend import AsyncSMTPBackend

logger = logging.getLogger(__name__)


class AsyncSMTPClientWithResponse:
    """Async SMTP client built on aiosmtplib that returns SMTPResponse objects."""

    def __init__(self, parent: AsyncSMTPBackend, **kwargs):
        self.parent = parent
        self.make_response = parent.make_response

        self.tls = kwargs.pop("tls", False)
        self.ssl = kwargs.pop("ssl", False)
        self.debug = kwargs.pop("debug", 0)
        if self.debug:
            logger.warning(
                "debug parameter is not supported in async mode; "
                "use Python logging instead"
            )
        self.user = kwargs.pop("user", None)
        self.password = kwargs.pop("password", None)

        # aiosmtplib uses use_tls for implicit TLS (SMTPS) and
        # start_tls for STARTTLS after connect
        smtp_kwargs = dict(kwargs)
        smtp_kwargs["use_tls"] = self.ssl
        smtp_kwargs["start_tls"] = self.tls

        # aiosmtplib uses 'hostname' instead of 'host'
        if "host" in smtp_kwargs:
            smtp_kwargs["hostname"] = smtp_kwargs.pop("host")

        self._smtp = aiosmtplib.SMTP(**smtp_kwargs)
        self._esmtp = False

    async def initialize(self):
        await self._smtp.connect()
        # connect() may have already completed EHLO internally
        self._esmtp = self._smtp.supports_esmtp
        try:
            if self._smtp.is_ehlo_or_helo_needed:
                try:
                    await self._smtp.ehlo()
                    self._esmtp = True
                except aiosmtplib.SMTPHeloError:
                    # aiosmtplib closes the transport on 421 responses
                    # before raising; don't attempt HELO on a dead connection
                    if not self._smtp.is_connected:
                        raise
                    await self._smtp.helo()
                    # aiosmtplib sets supports_esmtp before checking the
                    # response code, so it may be True even after EHLO
                    # failed.  Track the real state ourselves.
                    self._esmtp = False
            if self.user:
                await self._smtp.login(self.user, self.password)
        except Exception:
            await self.quit()
            raise

    async def quit(self):
        """Closes the connection to the email server."""
        try:
            await self._smtp.quit()
        except (aiosmtplib.SMTPServerDisconnected, ConnectionError):
            self._smtp.close()

    async def _rset(self):
        try:
            await self._smtp.rset()
        except (aiosmtplib.SMTPServerDisconnected, ConnectionError):
            pass

    async def sendmail(
        self,
        from_addr: str,
        to_addrs: list[str] | str,
        msg: bytes,
        mail_options: list[str] | None = None,
        rcpt_options: list[str] | None = None,
    ) -> SMTPResponse | None:

        if not to_addrs:
            return None

        rcpt_options = rcpt_options or []
        mail_options = mail_options or []
        esmtp_opts = []
        if self._esmtp:
            if self._smtp.supports_extension("size"):
                esmtp_opts.append("size=%d" % len(msg))
            for option in mail_options:
                esmtp_opts.append(option)

        response = self.make_response()

        from_addr = sanitize_email(from_addr)

        response.from_addr = from_addr
        response.esmtp_opts = esmtp_opts[:]

        try:
            resp = await self._smtp.mail(from_addr, options=esmtp_opts)
        except aiosmtplib.SMTPSenderRefused as exc:
            response.set_status(
                "mail",
                exc.code,
                exc.message.encode() if isinstance(exc.message, str) else exc.message,
            )
            response.set_exception(exc)
            await self._rset()
            return response

        response.set_status(
            "mail",
            resp.code,
            resp.message.encode() if isinstance(resp.message, str) else resp.message,
        )

        if resp.code != 250:
            await self._rset()
            response.set_exception(
                aiosmtplib.SMTPSenderRefused(resp.code, resp.message, from_addr)
            )
            return response

        if not isinstance(to_addrs, (list, tuple)):
            to_addrs = [to_addrs]

        to_addrs = [sanitize_email(e) for e in to_addrs]

        response.to_addrs = to_addrs
        response.rcpt_options = rcpt_options[:]
        response.refused_recipients = {}

        for a in to_addrs:
            try:
                resp = await self._smtp.rcpt(a, options=rcpt_options)
                code = resp.code
                resp_msg = (
                    resp.message.encode()
                    if isinstance(resp.message, str)
                    else resp.message
                )
            except aiosmtplib.SMTPRecipientRefused as exc:
                code = exc.code
                resp_msg = (
                    exc.message.encode()
                    if isinstance(exc.message, str)
                    else exc.message
                )

            response.set_status("rcpt", code, resp_msg, recipient=a)
            if (code != 250) and (code != 251):
                response.refused_recipients[a] = (code, resp_msg)

        if len(response.refused_recipients) == len(to_addrs):
            await self._rset()
            refused_list = [
                aiosmtplib.SMTPRecipientRefused(
                    code, msg.decode() if isinstance(msg, bytes) else msg, addr
                )
                for addr, (code, msg) in response.refused_recipients.items()
            ]
            response.set_exception(aiosmtplib.SMTPRecipientsRefused(refused_list))
            return response

        try:
            resp = await self._smtp.data(msg)
        except aiosmtplib.SMTPDataError as exc:
            resp_msg = (
                exc.message.encode() if isinstance(exc.message, str) else exc.message
            )
            response.set_status("data", exc.code, resp_msg)
            response.set_exception(exc)
            await self._rset()
            return response

        resp_msg = (
            resp.message.encode() if isinstance(resp.message, str) else resp.message
        )
        response.set_status("data", resp.code, resp_msg)
        if resp.code != 250:
            await self._rset()
            response.set_exception(aiosmtplib.SMTPDataError(resp.code, resp.message))
            return response

        response._finished = True
        return response
