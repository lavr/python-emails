# encoding: utf-8
from __future__ import annotations

from typing import Any


class Response:

    def __init__(self, exception: Exception | None = None, backend: Any = None) -> None:
        self.backend = backend
        self.set_exception(exception)
        self.from_addr: str | None = None
        self.to_addrs: list[str] | None = None
        self._finished: bool = False

    def set_exception(self, exc: Exception | None) -> None:
        self._exc = exc

    def raise_if_needed(self) -> None:
        if self._exc:
            raise self._exc

    @property
    def error(self) -> Exception | None:
        return self._exc

    @property
    def success(self) -> bool:
        return self._finished


class SMTPResponse(Response):

    def __init__(self, exception: Exception | None = None, backend: Any = None) -> None:

        super(SMTPResponse, self).__init__(exception=exception, backend=backend)

        self.responses: list[list] = []

        self.esmtp_opts: list[str] | None = None
        self.rcpt_options: list[str] | None = None

        self.status_code: int | None = None
        self.status_text: str | None = None
        self.last_command: str | None = None
        self.refused_recipients: dict[str, tuple[int, bytes]] = {}

    def set_status(self, command: str, code: int, text: str, **kwargs: Any) -> None:
        self.responses.append([command, code, text, kwargs])
        self.status_code = code
        self.status_text = text
        self.last_command = command

    @property
    def success(self) -> bool:
        return self._finished and self.status_code is not None and self.status_code == 250

    def __repr__(self) -> str:
        return "<emails.backend.SMTPResponse status_code=%s status_text=%s>" % (self.status_code.__repr__(),
                                                                                self.status_text.__repr__())

