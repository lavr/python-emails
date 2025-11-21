from typing import Any, Optional, Union, Tuple, List, Dict, Callable, TypeVar
import email.charset

_charsets_loaded: bool
CHARSETS_FIX: List[List[str]]

def load_email_charsets() -> None: ...

T = TypeVar('T')

class cached_property:
    func: Callable[[Any], T]
    def __init__(self, func: Callable[[Any], T]) -> None: ...
    def __get__(self, obj: Any, cls: Any) -> T: ...

class CachedDnsName:
    def __str__(self) -> str: ...
    def get_fqdn(self) -> str: ...

DNS_NAME: CachedDnsName

def decode_header(value: Union[str, bytes], default: str = ..., errors: str = ...) -> str: ...

class MessageID:
    domain: str
    idstring: str
    def __init__(self, domain: Optional[str] = ..., idstring: Optional[str] = ...) -> None: ...
    def __str__(self) -> str: ...
