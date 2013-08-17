# encoding: utf-8
from __future__ import unicode_literals, print_function
import logging
from cssutils.css import CSSStyleSheet
from cssutils import CSSParser
import cssutils

from emails.compat import urlparse, to_native, string_types, to_unicode, to_bytes, text_type


class PageStylesheets:

    """
    Store all html page styles and generates concatenated stylesheet
    """

    def __init__(self):
        self.urls = set()
        self._uri_properties = []
        self.sheets = []
        self.dirty = True
        self.element = None

    def update_tag(self):
        if self.element is not None:
            self._concatenate_sheets()
            cssText = self._cached_stylesheet.cssText
            cssText = cssText and to_unicode(cssText, 'utf-8') or ''
            self.element.text = cssText

    def attach_tag(self, element):
        self.element = element

    def append(self, url=None, text=None, absolute_url=None, local_loader=None):
        if (url is not None) and (url in self.urls):
            logging.debug('stylesheet url duplicate: %s', url)
            return
        self.sheets.append({'url': url, 'text': text, 'absolute_url': absolute_url or url, 'local_loader': local_loader})
        self.dirty = True

    def _concatenate_sheets(self):
        if self.dirty or (self._cached_stylesheet is None):
            r = CSSStyleSheet()
            uri_properties = []

            for d in self.sheets:
                local_loader = d.get('local_loader', None)
                text = d.get('text', None)
                uri = d.get('uri', None)
                absolute_url = d.get('absolute_url', None)

                if (text is None) and local_loader and uri:
                    text = local_loader[uri]

                if text:
                    sheet = CSSParser().parseString(text, href=absolute_url)
                else:
                    sheet = cssutils.parseUrl(href=absolute_url)

                for rule in sheet:
                    r.add(rule)
                    #print __name__, "rule=", rule
                    for p in _get_rule_uri_properties(rule):
                        #print __name__, "_get_rule_uri_properties:", p
                        uri_properties.append(p)

            self._uri_properties = uri_properties
            #print __name__, "self._uri_properties=", self._uri_properties
            self._cached_stylesheet = r
            self.dirty = False

    @property
    def stylesheet(self):
        self._concatenate_sheets()
        return self._cached_stylesheet

    @property
    def uri_properties(self):
        self._concatenate_sheets()
        return self._uri_properties


class StyledTagWrapper:

    def __init__(self, el):
        self.el = el
        self.style = CSSParser().parseStyle(el.get('style'))

    def update(self):
        cssText = self.style.cssText
        if isinstance(cssText, str):
            cssText = to_unicode(cssText, 'utf-8')
        self.el.set('style', cssText)

    def uri_properties(self):
        for p in self.style.getProperties(all=True):
            for v in p.propertyValue:
                if v.type == 'URI':
                    yield v


# Stuff for extracting 'uri-properties' from CSS
# Expired from cssutils examples

def _style_declarations(base):
    "recursive generator to find all CSSStyleDeclarations"
    if hasattr(base, 'cssRules'):
        for rule in base.cssRules:
            for s in _style_declarations(rule):
                yield s
    elif hasattr(base, 'style'):
        yield base.style


def _get_rule_uri_properties(rule):

    for style in _style_declarations(rule):
        for p in style.getProperties(all=True):
            for v in p.propertyValue:
                if v.type == 'URI':
                    yield v


def get_stylesheets_uri_properties(sheet):
    for rule in sheet:
        for p in _get_rule_uri_properties(rule):
            yield p
