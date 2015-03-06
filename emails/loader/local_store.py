# encoding: utf-8
from __future__ import unicode_literals
import logging
import mimetypes
import os
from os import path
import errno
from zipfile import ZipFile
import email

from emails.compat import to_unicode, string_types, to_native
from emails.loader.helpers import guess_html_charset, decode_text


class FileNotFound(Exception):
    pass


def split_template_path(template):
    """Split a path into segments and perform a sanity check.  If it detects
    '..' in the path it will raise a `TemplateNotFound` error.
    """
    pieces = []
    for piece in template.split('/'):
        if path.sep in piece \
                or (path.altsep and path.altsep in piece) or \
                        piece == path.pardir:
            raise FileNotFound(template)
        elif piece and piece != '.':
            pieces.append(piece)
    return pieces


def open_if_exists(filename, mode='rb'):
    """Returns a file descriptor for the filename if that file exists,
    otherwise `None`.
    """
    try:
        return open(filename, mode)
    except IOError as e:
        if e.errno not in (errno.ENOENT, errno.EISDIR):
            raise


class BaseLoader(object):

    def __getitem__(self, filename):
        try:
            contents, _ = self.get_file(filename)
            return contents
        except FileNotFound:
            return None

    def get_file(self, name):
        raise NotImplementedError

    def content(self, filename, is_html=False, decode=True, guess_charset=False, charset='utf-8'):
        data = self[filename]
        if decode:
            data, encoding = decode_text(data,
                                         is_html=is_html,
                                         guess_charset=guess_charset,
                                         try_common_charsets=False,
                                         fallback_charset=charset)
        return data

    def find_index_file(self, filename=None):
        if filename:
            if self[filename]:
                return filename
            else:
                raise FileNotFound(filename)

        html_files = []

        for filename in self.list_files():

            f = path.basename(filename).lower()

            if f.endswith('.htm') or f.endswith('.html'):
                if f.startswith('index.'):
                    return filename
                else:
                    html_files.append(filename)

        # Ignore hidden files (filename started with dot)
        for fn in filter(lambda p: not os.path.basename(p).startswith('.'), html_files):
            return fn

        raise FileNotFound('index html')


# FileSystemLoader from jinja2.loaders

class FileSystemLoader(BaseLoader):
    """Loads templates from the file system.  This loader can find templates
    in folders on the file system and is the preferred way to load them.

    The loader takes the path to the templates as string, or if multiple
    locations are wanted a list of them which is then looked up in the
    given order:

    >>> loader = FileSystemLoader('/path/to/templates')
    >>> loader = FileSystemLoader(['/path/to/templates', '/other/path'])

    Per default the template encoding is ``'utf-8'`` which can be changed
    by setting the `encoding` parameter to something else.
    """

    def __init__(self, searchpath, encoding='utf-8', base_path=None):
        if isinstance(searchpath, string_types):
            searchpath = [searchpath]
        self.searchpath = list(searchpath)
        self.encoding = encoding
        self.base_path = base_path

    def get_file(self, filename):
        if self.base_path:
            filename = path.join(self.base_path, filename)
        pieces = split_template_path(filename)
        for searchpath in self.searchpath:
            filename = path.join(searchpath, *pieces)
            f = open_if_exists(filename)
            if f is None:
                continue
            try:
                contents = f.read()
            finally:
                f.close()
            return contents, filename
        raise FileNotFound(filename)

    def list_files(self):
        found = set()
        for searchpath in self.searchpath:
            for dirpath, dirnames, filenames in os.walk(searchpath):
                for filename in filenames:
                    template = path.join(dirpath, filename) \
                        [len(searchpath):].strip(path.sep) \
                        .replace(path.sep, '/')
                    if template[:2] == './':
                        template = template[2:]
                    if template not in found:
                        yield template


class ZipLoader(BaseLoader):
    def __init__(self, file, encoding='utf-8', base_path=None, guess_encoding=True):
        self.zipfile = ZipFile(file, 'r')
        self.encoding = encoding
        self.base_path = base_path
        self.guess_encoding = guess_encoding
        self._filenames = None

    def _decode_zip_filename(self, name):
        for enc in ('cp866', 'cp1251', 'utf-8'):
            try:
                return to_unicode(name, enc)
            except UnicodeDecodeError:
                pass
        return name

    def _unpack_zip(self):
        if self._filenames is None:
            self._filenames = {}
            for name in self.zipfile.namelist():
                decoded_name = self._decode_zip_filename(name)
                self._filenames[decoded_name] = name

    def get_file(self, name):

        if self.base_path:
            name = path.join(self.base_path, name)

        self._unpack_zip()

        if isinstance(name, str):
            name = to_unicode(name, 'utf-8')

        original_name = self._filenames.get(name)

        if original_name is None:
            raise FileNotFound(name)

        return self.zipfile.read(original_name), name

    def list_files(self):
        self._unpack_zip()
        return sorted(self._filenames)


class MsgLoader(BaseLoader):
    """
    Load files from email.Message
    Thanks to
    http://blog.magiksys.net/parsing-email-using-python-content
    """

    common_charsets = ['ascii', 'utf-8', 'utf-16', 'windows-1252', 'cp850', 'windows-1251']

    def __init__(self, msg, base_path=None):
        if isinstance(msg, string_types):
            self.msg = email.message_from_string(msg)
        elif isinstance(msg, bytes):
            self.msg = email.message_from_string(to_native(msg))
        else:
            self.msg = msg
        self.base_path = base_path
        self._html_files = []
        self._text_files = []
        self._files = {}


    def decode_text(self, text, charset=None):
        if charset:
            try:
                return text.decode(charset), charset
            except UnicodeError:
                pass
        for charset in self.common_charsets:
            try:
                return text.decode(charset), charset
            except UnicodeError:
                pass
        return text, None

    def clean_content_id(self, content_id):
        if content_id.startswith('<'):
            content_id = content_id[1:]
        if content_id.endswith('>'):
            content_id = content_id[:-1]
        return content_id

    def extract_part_text(self, part):
        return self.decode_text(part.get_payload(decode=True), charset=part.get_param('charset'))[0]

    def add_html_part(self, part):
        name = '__index.html'
        self._files[name] = {'data': self.extract_part_text(part),
                             'filename': name,
                             'content_type': part.get_content_type()}

    def add_text_part(self, part):
        name = '__index.txt'
        self._files[name] = {'data': self.extract_part_text(part),
                             'filename': name,
                             'content_type': part.get_content_type()}

    def add_another_part(self, part):
        counter = 1
        f = {}
        content_id = part['Content-ID']
        if content_id:
            f['filename'] = self.clean_content_id(content_id)
            f['inline'] = True
        else:
            filename = part.get_filename()
            if not filename:
                ext = mimetypes.guess_extension(part.get_content_type())
                if not ext:
                    # Use a generic bag-of-bits extension
                    ext = '.bin'
                filename = 'part-%03d%s' % (counter, ext)
                counter += 1
            f['filename'] = filename
        f['content_type'] = part.get_content_type()
        f['data'] = part.get_payload(decode=True)
        self._files[f['filename']] = f

    def _parse_msg(self):
        for part in self.msg.walk():
            content_type = part.get_content_type()

            if content_type.startswith('multipart/'):
                continue

            if content_type == 'text/html':
                self.add_html_part(part)
                continue

            if content_type == 'text/plain':
                self.add_text_part(part)
                continue

            self.add_another_part(part)

    def get_file(self, name):
        self._parse_msg()
        f = self._files.get(name)
        if f:
            return f['data'], name
        raise FileNotFound(name)

    def list_files(self):
        return self._files