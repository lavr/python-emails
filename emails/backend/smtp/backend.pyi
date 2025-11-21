from typing import Any, Optional, Dict, List, Type, Callable
from ..response import SMTPResponse
from .client import SMTPClientWithResponse, SMTPClientWithResponse_SSL

class SMTPBackend:
    DEFAULT_SOCKET_TIMEOUT: int
    connection_cls: Type[SMTPClientWithResponse]
    connection_ssl_cls: Type[SMTPClientWithResponse_SSL]
    response_cls: Type[SMTPResponse]
    smtp_cls: Type[Any]
    ssl: bool
    tls: Optional[bool]
    smtp_cls_kwargs: Dict[str, Any]
    host: Optional[str]
    port: Optional[int]
    fail_silently: bool
    mail_options: List[str]
    _client: Optional[Any]

    def __init__(self, ssl: bool = ..., fail_silently: bool = ..., mail_options: Optional[List[str]] = ..., **kwargs: Any) -> None: ...
    def get_client(self) -> Any: ...
    def close(self) -> None: ...
    def make_response(self, exception: Optional[Exception] = ...) -> SMTPResponse: ...
    def retry_on_disconnect(self, func: Callable[..., Any]) -> Callable[..., Any]: ...
    def _send(self, **kwargs: Any) -> Any: ...
