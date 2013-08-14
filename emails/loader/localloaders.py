# encoding: utf-8

from os import path

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

        if filename and self[filename]:
            return filename
        else:
            raise FileNotFound(filename)

        html_files = []
        index_html = None

        for filename in self.list_files():
            f = os.path.basename(filename).lower()

            if f.endswith('.htm') or f.endswith('.html'):
                if f.startswith('index.'):
                    return filename
                else:
                    html_files.append(filename)

        if html_files:
            return htmlfiles[0]

        raise FileNotFound('index.htm')


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

    def __init__(self, searchpath, encoding='utf-8'):
        if isinstance(searchpath, basestring):
            searchpath = [searchpath]
        self.searchpath = list(searchpath)
        self.encoding = encoding

    def get_source(self, template):
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




