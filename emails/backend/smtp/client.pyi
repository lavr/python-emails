from typing import Any, Union, Sequence
from smtplib import SMTP, SMTP_SSL

class SMTPClientWithResponse(SMTP):
    parent: Any
    make_response: Any
    tls: bool
    ssl: bool
    debug: int
    # user: str
    # password: str
    _initialized: bool
    initialized: bool
    def __init__(self, parent: Any, **kwargs: Any) -> None: ...
    def initialize(self) -> None: ...
    def quit(self) -> Any: ...
    def _rset(self) -> None: ...
    def sendmail(self, from_addr: str, to_addrs: Union[str, Sequence[str]], msg: Any, mail_options: Sequence[str] = ..., rcpt_options: Sequence[str] = ...) -> Any: ...

class SMTPClientWithResponse_SSL(SMTP_SSL):
    parent: Any
    make_response: Any
    tls: bool
    ssl: bool
    debug: int
    # user: str
    # password: str
    _initialized: bool
    initialized: bool
    def __init__(self, parent: Any, **kwargs: Any) -> None: ...
    def initialize(self) -> None: ...
    def quit(self) -> Any: ...
    def _rset(self) -> None: ...
    def sendmail(self, from_addr: str, to_addrs: Union[str, Sequence[str]], msg: Any, mail_options: Sequence[str] = ..., rcpt_options: Sequence[str] = ...) -> Any: ...
