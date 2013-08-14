# encoding: utf-8

import posixpath
import os.path
from lxml import etree
import requests
import logging

from emails.compat import urlparse  # import urljoin, urlparse, urlsplit, urlunparse

from emails.store import MemoryFileStore, LazyHTTPFile
from .stylesheets import PageStylesheets, get_stylesheets_uri_properties, StyledTagWrapper

from .cssinliner import CSSInliner
from .helpers import guess_charset

from .wrappers import TAG_WRAPPER, CSS_WRAPPER

import helpers


class HTTPLoaderError(Exception):
    pass


class HTTPLoader:

    """
    HTML loader loads single html page and store it as some sort of web archive:
        * loads html page
        * loads linked images
        * loads linked css and images from css
        * converts css to inline html styles
    """

    USER_AGENT = 'python-emails/1.0'

    UNSAFE_TAGS = set( ['script', 'object', 'iframe', 'frame', 'base', 'meta', 'link', 'style'])
    TAGS_WITH_BACKGROUND = set(['td', 'tr', 'th', 'body'])
    TAGS_WITH_IMAGES = TAGS_WITH_BACKGROUND.union(set(['img', ]))
    CSS_MEDIA = ['', 'screen', 'all', 'email']

    tag_link_cls = {
        'a': TAG_WRAPPER('href'),
        'link': TAG_WRAPPER('href'),
        'img': TAG_WRAPPER('src'),
        'td':  TAG_WRAPPER('background'),
        'table':  TAG_WRAPPER('background'),
        'th':  TAG_WRAPPER('background'),
    }

    css_link_cls = CSS_WRAPPER

    attached_image_cls = LazyHTTPFile

    def __init__(self, filestore, encoding='utf-8', fetch_params=None):
        self.filestore = filestore
        self.encoding = encoding
        self.fetch_params = fetch_params
        self.stylesheets = PageStylesheets()
        self.base_url = None
        self._attachments = None

    def _fetch(self, url, valid_http_codes=(200, ), fetch_params = None):
        _params = dict(allow_redirects=True, verify=False,
                       headers={'User-Agent': self.USER_AGENT})
        fetch_params = fetch_params or self.fetch_params
        if fetch_params:
            _params.update(fetch_params)
        response = requests.get(url,  **_params)
        if valid_http_codes and (response.status_code not in valid_http_codes):
            raise HTTPLoaderError('Error loading url: %s. HTTP status: %s' % (url, response.http_status))
        return response

    def get_html_tree(self):
        return self._html_tree

    def set_html_tree(self, value):
        self._html_tree = value
        self._html = None  # We never actually store html, only cached html_tree render

    html_tree = property(get_html_tree, set_html_tree)

    def tag_has_link(self, tag):
        return tag in self.tag_link_cls

    def load_start(self, url, base_url=None, encoding=None, fetch_params=None):
        """
        Set some params and load start page
        """

        if encoding:
            self.encoding = encoding

        # Load start page
        response = self._fetch(url, valid_http_codes=(200, ), fetch_params=fetch_params)
        self.start_url = url
        self.base_url = base_url or url  # Fixme: split base_url carefully
        self.headers = response.headers
        content = response.content
        content = content.replace('\r\n', '\n')  # Remove \r, or we'll get much &#13;
        self.html_encoding = guess_charset(response.headers, content)
        self.html_content = content

    def make_html_tree(self):

        self.html_tree = etree.HTML(self.html_content, parser=etree.HTMLParser(encoding=self.html_encoding))
        # TODO: try another load methods, i.e. etree.fromstring(xml,
        # base_url="http://where.it/is/from.xml") ?

    def parse_html_tree(self, remove_unsafe_tags=True):

        # Parse html, load important tags
        # TODO: see also: http://softwaremaniacs.org/forum/django/14909/

        self._a_links = []
        self._tags_with_links = []
        self._tags_with_images = []

        for el in self.html_tree.iter():

            if el.tag == 'img' or el.tag == 'a' or self.tag_has_link(el.tag):
                self.process_tag_with_link(el)

            if el.tag == 'base':
                self.base_url = el.get('href')  # TODO: can be relative link in BASE HREF ?

            elif el.tag == 'link':
                self.process_external_css_tag(el)

            elif el.tag == 'style':
                self.process_style_tag(el)

            # elif el.tag=='a':
            #    self.process_a_tag( el )

            if el.get('style'):
                self.process_tag_with_style(el)

            if remove_unsafe_tags and (el.tag in self.UNSAFE_TAGS):
                # Remove unsafe tags
                # self._removed_unsafe.append(el)  # Save it for reports
                p = el.getparent()
                if (p is not None):
                    p.remove(el)

        # now make concatenated stylesheet
        stylesheet = self.stylesheets.stylesheet

        for prop in self.stylesheets.uri_properties:
            self.process_stylesheet_uri_property(prop)

    def load_url(self,
                 url,
                 base_url=None,
                 css_inline=True,
                 remove_unsafe_tags=True,
                 make_links_absolute=False,
                 set_content_type_meta=True,
                 update_stylesheet=False
                 ):

        self.load_start(url=url, base_url=base_url)
        self.make_html_tree()
        self.parse_html_tree(remove_unsafe_tags=remove_unsafe_tags)

        if make_links_absolute:
            [self.make_link_absolute(obj) for obj in self.iter_image_links()]
            [self.make_link_absolute(obj) for obj in self.iter_a_links()]

        if remove_unsafe_tags and update_stylesheet:
            self.insert_big_stylesheet()

        # self.process_attaches()

        # TODO: process images in self._tags_with_styles
        if css_inline:
            self.doinlinecss()
            # self.doinlinecss_pynliner()

        if set_content_type_meta:
            self.set_content_type_meta()

    def process_external_css_tag(self, el):
        """
        Process <link href="..." rel="stylesheet">
        """
        if el.get('rel', '') == 'stylesheet' and el.get('media', '') in self.CSS_MEDIA:
            #logging.debug('Found link %s, rel=%s, media=%s', el, el.get('rel',''), el.get('media',''))
            url = el.get('href', '')
            if url:
                self.stylesheets.append(url=url, absolute_url=self.absolute_url(url))

    def process_style_tag(self, el):
        """
        Process: <style>...</style>
        """
        if el.text:
            self.stylesheets.append(text=el.text, url=self.start_url)

    def iter_image_links(self):
        return (_ for _ in self._tags_with_images)

    def iter_a_links(self):
        return (_ for _ in self._a_links)

    def process_tag_with_link(self, el):
        """
        Process IMG SRC, TABLE BACKGROUND, ...
        """
        obj = self.tag_link_cls[el.tag](el)
        self._tags_with_links.append(obj)
        if el.tag in self.TAGS_WITH_IMAGES:
            lnk = obj.link
            if lnk is not None:
                self._tags_with_images.append(obj)
                # print __name__, "process_tag_with_link", obj.el.attrib, obj.el.tag , obj.link
                self.attach_image(uri=lnk, absolute_url=self.absolute_url(lnk))
        elif el.tag == 'a':
            self._a_links.append(obj)

    def attach_image(self, uri, absolute_url, subtype=None):
        if uri not in self.filestore:
            self.filestore.add(self.attached_image_cls(
                uri=uri, absolute_url=absolute_url, subtype=subtype, fetch_params=self.fetch_params))

    def process_tag_with_style(self, el):
        t = StyledTagWrapper(el)
        for p in t.uri_properties():
            obj = self.css_link_cls(p, updateme=t)
            self._tags_with_links.append(obj)

    def process_stylesheet_uri_property(self, prop):
        self._tags_with_links.append(self.css_link_cls(prop))

    def make_link_absolute(self, obj):
        link = obj.link
        if link:
            obj.link = self.absolute_url(link)

    def set_content_type_meta(self):
        _tree = self.html_tree
        new_document = helpers.set_content_type_meta(_tree, element_cls=etree.Element)
        if _tree != new_document:
            # document may be updated here (i.e. html tag added)
            self.html_tree = new_document

    def insert_big_stylesheet(self):
        helpers.add_body_stylesheet(self.html_tree,
                                    element_cls=etree.Element,
                                    tag="body",
                                    cssText=unicode(self.stylesheets.stylesheet.cssText, 'utf-8'))

    def absolute_url(self, url, base_url=None):

        # In: some url
        # Out: (absolute_url, relative_url) based on self._base_url

        if base_url is None:
            base_url = self.base_url

        parsed_url = urlparse.urlsplit(url)
        if parsed_url.scheme:
            # is absolute_url
            return url
        else:
            # http://xxx.com/../../template/overdoze_team/css/style.css -> http://xxx.com/template/overdoze_team/css/style.css
            # см. http://teethgrinder.co.uk/perm.php?a=Normalize-URL-path-python
            joined = urlparse.urljoin(self.base_url, url)
            url = urlparse.urlparse(joined)
            path = posixpath.normpath(url[2])
            return urlparse.urlunparse((url.scheme, url.netloc, path, url.params, url.query, url.fragment))

    def doinlinecss(self):
        self.html_tree = CSSInliner(css=self.stylesheets.stylesheet).transform(html=self.html_tree)

    def doinlinecss_pynliner(self):
        # pynliner is bit accurate with complex css, but not ideal and much slower
        # todo: make comparison pynliner vs cssinliner
        import pynliner
        css_text = unicode(self.stylesheet.cssText, 'utf-8')
        html = pynliner.Pynliner().from_string(self.html).with_cssString(css_text).run()
        self.html_tree = etree.HTML(html, parser=etree.HTMLParser(encoding='utf-8'))

    @property
    def html(self):
        self._html = etree.tostring(self.html_tree, encoding=self.encoding, method='xml')
        return self._html

    @property
    def attachments_dict(self):
        return list(self.filestore.as_dict())

    def save_to_file(self, filename):
        path = os.path.abspath(filename)
        # Save images locally and replace all links to images in html
        files_dir = '_files'
        _rename_map = {}

        for obj in self.iter_image_links():
            #print __name__, "save_to_file: process link %s %s" % (obj.el, obj.link)
            uri = obj.link
            if uri is None:
                continue
            _new_uri = _rename_map.get(uri, None)
            if _new_uri is None:
                file = self.filestore.by_uri(uri, synonims=obj.link_history)
                if file is None:
                    logging.warning(
                        'file "%s" not found in attachments, this should not happen. skipping', uri)
                    continue
                _new_uri = _rename_map[uri] = os.path.join(files_dir, file.filename)
            obj.link = _new_uri

        try:
            os.makedirs(files_dir)
        except OSError:
            pass
        for attach in self.filestore:
            #print __name__, "saving attach %s" % attach.uri
            attach.fetch()
            new_uri = _rename_map.get(attach.uri)
            if new_uri:
                print __name__, "news uri: %s" % new_uri
                attach.uri = new_uri
                open(new_uri, 'wb').write(attach.data)

        open(filename, 'w').write(self.html)
