# encoding: utf-8
from __future__ import unicode_literals
from os.path import splitext
from emails.compat import OrderedDict, string_types, to_unicode

from .file import BaseFile

# class FileNotFound(Exception):
#    pass


class FileStore(object):
    pass


class MemoryFileStore(FileStore):

    file_cls = BaseFile

    def __init__(self, file_cls=None):
        if file_cls:
            self.file_cls = file_cls
        self._files = OrderedDict()
        self._filenames = set()

    def __contains__(self, k):
        if isinstance(k, self.file_cls):
            return k.url in self._files
        elif isinstance(k, str):
            return k in self._files
        else:
            return False

    def keys(self):
        return list(self._files.keys())

    def __len__(self):
        return len(self._files)

    def as_dict(self):
        for d in self._files.values():
            yield d.as_dict()

    def remove(self, uri):
        # print __name__, "remove %s %s" % (uri, type(uri))
        if isinstance(uri, self.file_cls):
            uri = uri.uri

        assert isinstance(uri, string_types)

        v = self[uri]
        if v:
            filename = v.filename
            if filename and (filename in self._filenames):
                self._filenames.remove(filename)
            del self._files[uri]

    def unique_filename(self, filename):

        if filename not in self._filenames:
            return filename

        n = 1
        basefilename, ext = splitext(filename)

        while True:
            n += 1
            filename = "%s-%d%s" % (basefilename, n, ext)
            if filename not in self._filenames:
                return filename

    def add(self, value):

        if isinstance(value, self.file_cls):
            uri = value.uri
        elif isinstance(value, dict):
            value = self.file_cls(**value)
            uri = value.uri
        else:
            raise ValueError("Unknown file type: %s" % type(value))

        self.remove(uri)
        value.filename = self.unique_filename(value.filename)
        self._filenames.add(value.filename)
        self._files[uri] = value

    def by_uri(self, uri, synonims=None):
        r = self._files.get(uri, None)
        if r:
            return r
        if synonims:
            for _uri in synonims:
                r = self._files.get(_uri, None)
                if r:
                    return r
        return None

    def __getitem__(self, uri):
        return self._files.get(uri, None)

    def __iter__(self):
        for k in self._files:
            yield self._files[k]
