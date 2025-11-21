from typing import Any, Optional, List, Dict, Tuple

class Response:
    backend: Any
    _exc: Optional[Exception]
    from_addr: Optional[str]
    to_addrs: Optional[List[str]]
    _finished: bool
    def __init__(self, exception: Optional[Exception] = ..., backend: Any = ...) -> None: ...
    def set_exception(self, exc: Exception) -> None: ...
    def raise_if_needed(self) -> None: ...
    @property
    def error(self) -> Optional[Exception]: ...
    @property
    def success(self) -> bool: ...

class SMTPResponse(Response):
    responses: List[Any]
    esmtp_opts: Optional[List[str]]
    rcpt_options: Optional[List[str]]
    status_code: Optional[int]
    status_text: Optional[str]
    last_command: Optional[str]
    refused_recipient: Dict[str, Any]
    refused_recipients: Dict[str, Any]
    def __init__(self, exception: Optional[Exception] = ..., backend: Any = ...) -> None: ...
    def set_status(self, command: str, code: int, text: str, **kwargs: Any) -> None: ...
