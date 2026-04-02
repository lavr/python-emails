
from .backend import SMTPBackend

try:
    from .aio_backend import AsyncSMTPBackend
except ImportError:
    pass