from typing import Any, Optional, List, Tuple, Union, Pattern

class ReRules:
    re_meta: Pattern[Any]
    re_is_http_equiv: Pattern[Any]
    re_parse_http_equiv: Pattern[Any]
    re_charset: Pattern[Any]
    def __init__(self, conv: Optional[Any] = ...) -> None: ...

RULES_U: ReRules
RULES_B: ReRules

def guess_text_charset(text: Union[str, bytes], is_html: bool = ...) -> Optional[str]: ...
def guess_html_charset(html: Union[str, bytes]) -> Optional[str]: ...
def guess_charset(headers: Any, html: Union[str, bytes]) -> Optional[str]: ...

COMMON_CHARSETS: Tuple[str, ...]

def decode_text(text: Union[str, bytes],
                is_html: bool = ...,
                guess_charset: bool = ...,
                try_common_charsets: bool = ...,
                charsets: Optional[List[str]] = ...,
                fallback_charset: str = ...) -> Tuple[str, Optional[str]]: ...
