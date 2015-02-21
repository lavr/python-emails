# encoding: utf-8
from __future__ import unicode_literals
import posixpath
import os.path
import logging
import re
import warnings
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


def _add_content_type_meta(document, element_cls, content_type="text/html", charset="utf-8"):

    def _get_content_type_meta(head):
        content_type_meta = None
        for meta in head.find('meta') or []:
            http_equiv = meta.get('http-equiv', None)
            if http_equiv and (http_equiv.lower() == 'content_type'):
                content_type_meta = meta
                break
        if content_type_meta is None:
            content_type_meta = element_cls('meta')
            head.append(content_type_meta)
        return content_type_meta

    head = document.find('head')
    if not head:
        logging.warning('HEAD not found. This should not happen. Skip.')
        return

    meta = _get_content_type_meta(head)
    meta.set('content', '%s; charset=%s' % (content_type, charset))
    meta.set('http-equiv', "Content-Type")

    return document


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

    UNSAFE_TAGS = ['script', 'object', 'iframe', 'frame', 'base', 'meta', 'link', 'style']

    attachment_store_cls = MemoryFileStore
    attachment_file_cls = LazyHTTPFile

    def __init__(self, html, local_loader=None,
                 attachment_store=None,
                 requests_params=None,
                 css_inline=True,
                 remove_unsafe_tags=True,
                 make_links_absolute=True,
                 set_content_type_meta=True,
                 update_stylesheet=True,
                 images_inline=False,
                 **kw):
        self.attachment_store = attachment_store or self.attachment_store_cls()
        self.requests_params = requests_params
        self.local_loader = local_loader
        self.method = kw.get('method', 'html')
        self.root = _html_to_tree(html, method=self.method)
        self.premailer = PremailerWithLocalLoader(html=self.root, local_loader=self.local_loader, **kw)
        self.base_url = kw.get('base_url', None)

        self.remove_unsafe_tags = remove_unsafe_tags
        self.set_content_type_meta = set_content_type_meta
        self.images_inline = images_inline

        if not make_links_absolute:
            # Now we use Premailer that always makes links absolute
            warnings.warn("make_links_absolute=False is deprecated.", DeprecationWarning)

        if not css_inline:
            # Premailer always makes inline css.
            warnings.warn("css_inline=False is deprecated.", DeprecationWarning)

        if update_stylesheet:
            # Premailer has no such feature.
            warnings.warn("update_stylesheet=True is deprecated.", DeprecationWarning)



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

    def _remove_unsafe_tags(self):
        for tag in self.UNSAFE_TAGS:
            for el in self.root.xpath(".//%s" % tag):
                parent = el.getparent()
                if parent:
                    parent.remove(el)

    def transform(self):

        # 1. Premailer make some transformations on self.root tree:
        #  - load external css and make css inline
        #  - make absolute href and src if base_url is set
        self.premailer.transform()

        # 2. Load linked images and transform links
        self.apply_to_images(self._load_attachment)

        # 3. Remove unfase tags is requested
        if self.remove_unsafe_tags:
            self._remove_unsafe_tags()

        # 4. Set <meta> content-type
        if self.set_content_type_meta:
            # TODO: check if this useful
            _add_content_type_meta(self.root, element_cls=etree.Element)

        # 5. Make images inline
        if self.images_inline:
            return NotImplemented