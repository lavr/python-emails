# encoding: utf-8
import logging
from os import path
from zipfile import ZipFile

# FileSystemLoader adapted from jinja2.loaders

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
    except IOError, e:
        if e.errno not in (errno.ENOENT, errno.EISDIR):
            raise


class BaseLoader(object):

    def __getitem__(self, filename):
        try:
            contents, _ = self.get_source(filename)
            return contents
        except FileNotFound:
            return None

    def find_index_file(self, filename=None):
        #print __name__, "BaseLoader.find_index_file", filename
        if filename:
            if self[filename]:
                return filename
            else:
                raise FileNotFound(filename)

        html_files = []
        index_html = None

        for filename in self.list_files():

            f = path.basename(filename).lower()

            #print __name__, "BaseLoader.find_index_file", filename, f

            if f.endswith('.htm') or f.endswith('.html'):
                if f.startswith('index.'):
                    return filename
                else:
                    html_files.append(filename)

        if html_files:
            return htmlfiles[0]

        raise FileNotFound('index html')


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
        if isinstance(searchpath, basestring):
            searchpath = [searchpath]
        self.searchpath = list(searchpath)
        self.encoding = encoding
        self.base_path = base_path

    def get_source(self, template):

        if self.base_path:
            name = path.join(self.base_path, template)

        pieces = split_template_path(template)
        for searchpath in self.searchpath:
            filename = path.join(searchpath, *pieces)
            f = open_if_exists(filename)
            if f is None:
                continue
            try:
                contents = f.read().decode(self.encoding)
            finally:
                f.close()

            return contents, filename

        raise FileNotFound(template)

    def list_files(self):
        found = set()
        for searchpath in self.searchpath:
            for dirpath, dirnames, filenames in os.walk(searchpath):
                for filename in filenames:
                    template = os.path.join(dirpath, filename) \
                        [len(searchpath):].strip(os.path.sep) \
                                          .replace(os.path.sep, '/')
                    if template[:2] == './':
                        template = template[2:]
                    if template not in found:
                        yield template



class ZipLoader(BaseLoader):

    def __init__(self, file, encoding='utf-8', base_path=None):
        self.zipfile = ZipFile(file, 'r')
        self.encoding = encoding
        self.base_path = base_path
        self.mapping = {}
        self._filenames = None


    def _decode_zip_filename(self, name):
        for enc in ('cp866', 'cp1251', 'utf-8'):
            try:
                return unicode(name, 'cp866')
            except UnicodeDecodeError:
                pass
        return name


    def _unpack_zip(self):
        if self._filenames is None:
            self._filenames = {}
            for name in self.zipfile.namelist():
                decoded_name = self._decode_zip_filename(name)
                self._filenames[decoded_name] = name


    def get_source(self, name):

        logging.debug('ZipLoader.get_source %s', name)

        if self.base_path:
            name = path.join(self.base_path, name)
            logging.debug('ZipLoader.get_source has base_path, result name is %s', name)

        self._unpack_zip()

        if isinstance(name, str):
            name = unicode(name, 'utf-8')

        data = self.mapping.get(name, None)

        if data is not None:
            return data, name

        original_name = self._filenames.get(name)

        logging.debug('ZipLoader.get_source original_name=%s', original_name)

        if original_name is None:
            raise FileNotFound(name)

        data = self.zipfile.read(original_name)

        logging.debug('ZipLoader.get_source returns %s bytes', len(data))
        return data, name


    def list_files(self):
        self._unpack_zip()
        return sorted(self._filenames)


