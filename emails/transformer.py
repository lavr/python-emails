# encoding: utf-8
from __future__ import unicode_literals
import posixpath
import os.path
import logging
import re
from cssutils import CSSParser
from lxml import etree
from premailer import Premailer
from premailer.premailer import ExternalNotFoundError

from emails.compat import urlparse, to_unicode, to_bytes, text_type
from emails.store import MemoryFileStore, LazyHTTPFile
from .loader.local_store import FileNotFound


class PremailerWithLocalLoader(Premailer):

    def __init__(self, html, local_loader=None, **kw):
        self.local_loader = local_loader
        super(PremailerWithLocalLoader, self).__init__(html=html, **kw)

    def _load_external(self, url):
        """
        loads an external stylesheet from a remote url or local store
        """
        if url.startswith('//'):
            # then we have to rely on the base_url
            if self.base_url and 'https://' in self.base_url:
                url = 'https:' + url
            else:
                url = 'http:' + url

        if url.startswith('http://') or url.startswith('https://'):
            content = self._load_external_url(url)
        else:
            content = None

            if self.local_loader:
                try:
                    content = self.local_loader.get_source(url)
                except FileNotFound:
                    content = None

            if content is None:
                if self.base_url:
                    return self._load_external(urlparse.urljoin(self.base_url, url))
                else:
                    raise ExternalNotFoundError(url)

        return content


def _html_to_tree(html, method="html"):
    if method == 'xml':
        parser = etree.XMLParser(
            ns_clean=False,
            resolve_entities=False
        )
    else:
        parser = etree.HTMLParser()
    stripped = html.strip()
    return etree.fromstring(stripped, parser)

    """
    tree = etree.fromstring(stripped, parser).getroottree()
    page = tree.getroot()
    # lxml inserts a doctype if none exists, so only include it in
    # the root if it was in the original html.
    return tree if stripped.startswith(tree.docinfo.doctype) else page
    """

_cdata_regex = re.compile(r'\<\!\[CDATA\[(.*?)\]\]\>', re.DOTALL)

def _tree_to_html(tree, method="html", encoding='utf-8', **kwargs):
    out = etree.tostring(tree, encoding=encoding, method=method, **kwargs).decode(encoding)
    if method == 'xml':
        out = _cdata_regex.sub(
            lambda m: '/*<![CDATA[*/%s/*]]>*/' % m.group(1),
            out
        )
    return out



class Transformer(object):

    attachment_store_cls = MemoryFileStore
    attachment_file_cls = LazyHTTPFile

    def __init__(self, html, local_loader=None,
                 attachment_store=None,
                 requests_params=None, **kw):
        self.attachment_store = attachment_store or self.attachment_store_cls()
        self.requests_params = requests_params
        self.local_loader = local_loader
        self.method = kw.get('method', 'html')
        self.root = _html_to_tree(html, method=self.method)
        self.premailer = PremailerWithLocalLoader(html=self.root, local_loader=self.local_loader, **kw)
        self.base_url = kw.get('base_url', None)


    def to_string(self, encoding='utf-8', **kwargs):
        return _tree_to_html(self.root, encoding=encoding, **kwargs)

    def get_absolute_url(self, url):

        if not self.base_url:
            return url

        if url.startswith('//'):
            if 'https://' in self.base_url:
                url = 'https:' + url
            else:
                url = 'http:' + url
            return url

        if not (url.startswith('http://') or url.startswith('https://')):
            url = urlparse.urljoin(self.base_url, posixpath.normpath(url))

        return url

    def _load_attachment(self, uri, element=None, **kw):
        #
        # Load uri from remote url or from local_store
        # Return local uri
        #
        attachment = self.attachment_store.by_uri(uri)
        if attachment is None:
            attachment = self.attachment_file_cls(
                uri=uri,
                absolute_url=self.get_absolute_url(uri),
                local_loader=self.local_loader)
            self.attachment_store.add(attachment)
        return attachment.filename

    def apply_to_images(self, func, images=True, backgrounds=True, styles_uri=True):

        def _apply_to_style_uri(style_text, func):
            dirty = False
            parser = CSSParser().parseStyle(style_text)
            for prop in parser.getProperties(all=True):
                for value in prop.propertyValue:
                    if value.type == 'URI':
                        old_uri = value.uri
                        new_uri = func(old_uri, element=value)
                        if new_uri != old_uri:
                            dirty = True
                            value.uri = new_uri
            if dirty:
                return to_unicode(parser.cssText, 'utf-8')
            else:
                return style_text

        if images:
            # Apply to images from IMG tag
            for img in self.root.xpath(".//img"):
                img.attrib['src'] = func(img.attrib['src'], element=img)

        if backgrounds:
            # Apply to images from <tag background="X">
            for item in self.root.xpath("//@background"):
                tag = item.getparent()
                tag.attrib['background'] = func(tag.attrib['background'], element=tag)

        if styles_uri:
            # Apply to style uri
            for item in self.root.xpath("//@style"):
                tag = item.getparent()
                tag.attrib['style'] = _apply_to_style_uri(tag.attrib['style'], func=func)


    def apply_to_links(self, func):
        # Apply to images from IMG tag
        for a in self.root.xpath(".//a"):
            a.attrib['href'] = func(a.attrib['href'], element=a)


    def transform(self):

        # 1. Premailer make some transformations on self.root tree:
        #  - load external css and make css inline
        #  - make absolute href and src if base_url is set
        self.premailer.transform()

        # 2. Load linked images and transform links
        self.apply_to_images(self._load_attachment)