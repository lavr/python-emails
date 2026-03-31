from __future__ import annotations

import uuid
from mimetypes import guess_type
import puremagic
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from os.path import basename
from typing import Any, IO

import urllib.parse as urlparse

from ..utils import fetch_url, encode_header


MIMETYPE_UNKNOWN = 'application/unknown'


def fix_content_type(content_type: str | None, t: str = 'image') -> str:
    if not content_type:
        return "%s/unknown" % t
    else:
        return content_type


class BaseFile:

    """
    Store base "attachment-file" information.
    """

    _data: bytes | str | IO[bytes] | None

    def __init__(self, **kwargs: Any) -> None:
        """
        uri and filename are connected properties.
        if no filename set, filename extracted from uri.
        if no uri, but filename set, then uri==filename
        """
        self.uri = kwargs.get('uri', None)
        self.absolute_url: str | None = kwargs.get('absolute_url', None) or self.uri
        self.filename = kwargs.get('filename', None)
        self.data = kwargs.get('data', None)
        self._mime_type: str | None = kwargs.get('mime_type')
        self._headers: dict[str, str] = kwargs.get('headers', {})
        self._content_id: str | None = kwargs.get('content_id')
        self._content_disposition: str | None = kwargs.get('content_disposition', 'attachment')
        self.subtype: str | None = kwargs.get('subtype')
        self.local_loader = kwargs.get('local_loader')

    def as_dict(self, fields: tuple[str, ...] | None = None) -> dict[str, Any]:
        fields = fields or ('uri', 'absolute_url', 'filename', 'data',
                            'mime_type', 'content_disposition', 'subtype')
        return dict([(k, getattr(self, k)) for k in fields])

    def get_data(self) -> bytes | str | None:
        _data = self._data
        if isinstance(_data, (str, bytes)):
            return _data
        elif _data is None:
            return None
        else:
            return _data.read()

    def set_data(self, value: bytes | str | IO[bytes] | None) -> None:
        self._data = value

    data = property(get_data, set_data)

    def get_uri(self) -> str | None:
        _uri = getattr(self, '_uri', None)
        if _uri is None:
            _filename = getattr(self, '_filename', None)
            if _filename:
                _uri = self._uri = _filename
        return _uri

    def set_uri(self, value: str | None) -> None:
        self._uri = value

    uri = property(get_uri, set_uri)

    def get_filename(self) -> str | None:
        _filename = getattr(self, '_filename', None)
        if _filename is None:
            _uri = getattr(self, '_uri', None)
            if _uri:
                parsed_path = urlparse.urlparse(_uri)
                _filename = basename(parsed_path.path)
                if not _filename:
                    _filename = str(uuid.uuid4())
                self._filename = _filename
        return _filename

    def set_filename(self, value: str | None) -> None:
        self._filename = value

    filename = property(get_filename, set_filename)

    def get_mime_type(self) -> str:
        r = getattr(self, '_mime_type', None)
        if r is None:
            filename = self.filename
            if filename:
                r = self._mime_type = guess_type(filename)[0]
        if not r:
            _data = self._data
            if isinstance(_data, bytes):
                try:
                    r = puremagic.from_string(_data, mime=True)
                except puremagic.PureError:
                    pass
            elif isinstance(_data, str):
                try:
                    r = puremagic.from_string(_data.encode(), mime=True)
                except puremagic.PureError:
                    pass
        if not r:
            r = MIMETYPE_UNKNOWN
        self._mime_type = r
        return r

    mime_type = property(get_mime_type)

    def get_content_disposition(self) -> str | None:
        return getattr(self, '_content_disposition', None)

    def set_content_disposition(self, value: str | None) -> None:
        self._content_disposition = value

    content_disposition = property(get_content_disposition, set_content_disposition)

    @property
    def is_inline(self):
        return self.content_disposition == 'inline'

    @is_inline.setter
    def is_inline(self, value):
        if bool(value):
            self.content_disposition = 'inline'
        else:
            self.content_disposition = 'attachment'

    @property
    def content_id(self) -> str | None:
        if self._content_id is None:
            self._content_id = self.filename
        return self._content_id

    @property
    def mime(self) -> MIMEBase | None:
        content_disposition = self.content_disposition
        if content_disposition is None:
            return None
        p = getattr(self, '_cached_part', None)
        if p is None:
            filename_header = encode_header(self.filename)
            p = MIMEBase(*self.mime_type.split('/', 1), name=filename_header)
            data = self.data
            if isinstance(data, str):
                payload = data.encode()
            elif data is not None:
                payload = bytes(data)
            else:
                payload = b''
            p.set_payload(payload)
            encode_base64(p)
            if 'content-disposition' not in self._headers:
                p.add_header('Content-Disposition', self.content_disposition, filename=filename_header)
            if content_disposition == 'inline' and 'content-id' not in self._headers:
                p.add_header('Content-ID', '<%s>' % self.content_id)
            for (k, v) in self._headers.items():
                p.add_header(k, v)
            self._cached_part = p
        return p

    def reset_mime(self) -> None:
        self._mime = None

    def fetch(self) -> None:
        pass


class LazyHTTPFile(BaseFile):

    def __init__(self, requests_args: dict[str, Any] | None = None, **kwargs: Any) -> None:
        BaseFile.__init__(self, **kwargs)
        self.requests_args = requests_args
        self._fetched = False

    def fetch(self) -> None:
        if (not self._fetched) and self.uri:
            if self.local_loader:
                data = self.local_loader[self.uri]

                if data:
                    self._fetched = True
                    self._data = data
                    return

            r = fetch_url(url=self.absolute_url or self.uri, requests_args=self.requests_args)
            if r.status_code == 200:
                self._data = r.content
                self._headers = r.headers
                self._mime_type = fix_content_type(r.headers.get('content-type'), t='unknown')
                self._fetched = True

    def get_data(self) -> bytes | str:
        self.fetch()
        data = self._data
        if data is None:
            return ''
        if isinstance(data, (str, bytes)):
            return data
        return data.read()

    def set_data(self, v: bytes | str | IO[bytes] | None) -> None:
        self._data = v

    data = property(get_data, set_data)

    @property
    def mime_type(self) -> str:
        self.fetch()
        return self.get_mime_type()

    @property
    def headers(self) -> dict[str, str]:
        self.fetch()
        return self._headers
