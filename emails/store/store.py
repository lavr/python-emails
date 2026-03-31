from __future__ import annotations

from collections import OrderedDict
from collections.abc import Generator, Iterator
from os.path import splitext
from typing import Any

from .file import BaseFile


class FileStore:
    pass


class MemoryFileStore(FileStore):

    file_cls: type[BaseFile] = BaseFile

    def __init__(self, file_cls: type[BaseFile] | None = None) -> None:
        if file_cls:
            self.file_cls = file_cls
        self._files: OrderedDict[str, BaseFile] = OrderedDict()
        self._filenames: dict[str, str | None] = {}

    def __contains__(self, k: BaseFile | str | Any) -> bool:
        if isinstance(k, self.file_cls):
            return k.uri in self._files
        elif isinstance(k, str):
            return k in self._files
        else:
            return False

    def keys(self) -> list[str]:
        return list(self._files.keys())

    def __len__(self) -> int:
        return len(self._files)

    def as_dict(self) -> Generator[dict[str, Any], None, None]:
        for d in self._files.values():
            yield d.as_dict()

    def remove(self, uri: BaseFile | str) -> None:
        if isinstance(uri, self.file_cls):
            uri = uri.uri

        assert isinstance(uri, str)

        v = self[uri]
        if v:
            filename = v.filename
            if filename and (filename in self._filenames):
                del self._filenames[filename]
            del self._files[uri]

    def unique_filename(self, filename: str | None, uri: str | None = None) -> str | None:

        if filename in self._filenames:
            n = 1
            basefilename, ext = splitext(filename)

            while True:
                n += 1
                filename = "%s-%d%s" % (basefilename, n, ext)
                if filename not in self._filenames:
                    break

        if filename is not None:
            self._filenames[filename] = uri

        return filename

    def add(self, value: BaseFile | dict[str, Any], replace: bool = False) -> BaseFile:

        if isinstance(value, self.file_cls):
            uri = value.uri
        elif isinstance(value, dict):
            value = self.file_cls(**value)
            uri = value.uri
        else:
            raise ValueError("Unknown file type: %s" % type(value))

        if (uri not in self._files) or replace:
            self.remove(uri)
            value.filename = self.unique_filename(value.filename, uri=uri)
            self._files[uri] = value

        return value

    def by_uri(self, uri: str) -> BaseFile | None:
        return self._files.get(uri, None)

    def by_filename(self, filename: str) -> BaseFile | None:
        uri = self._filenames.get(filename)
        if uri:
            return self.by_uri(uri)
        return None

    def __getitem__(self, uri: str) -> BaseFile | None:
        return self.by_uri(uri) or self.by_filename(uri)

    def __iter__(self) -> Iterator[BaseFile]:
        for k in self._files:
            yield self._files[k]
