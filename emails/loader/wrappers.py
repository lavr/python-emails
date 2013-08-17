# encoding: utf-8

# tag-with-link wrapper
from __future__ import unicode_literals
import logging
from emails.compat import OrderedSet, to_unicode


class ElementWithLink(object):

    LINK_ATTR_NAME = None

    def __init__(self, el, encoding=None):
        self.el = el
        self._link_history = OrderedSet()
        self.encoding = encoding

    def get_link(self):
        #print(__name__, "ElementWithLink encoding=", self.encoding)
        return to_unicode(self.el.get(self.LINK_ATTR_NAME), self.encoding)

    def set_link(self, new):
        _old = self.get_link()
        if _old != new:
            logging.debug('Update link %s => %s ', _old, new)
            self.el.set(self.LINK_ATTR_NAME, new)
            self._link_history.add(_old)

    link = property(get_link, set_link)

    @classmethod
    def make(cls, attr):
        def wrapper(el, encoding):
            r = cls(el, encoding=encoding)
            r.LINK_ATTR_NAME = attr
            return r
        return wrapper

    @property
    def link_history(self):
        return self._link_history


class A_link(ElementWithLink):
    # el is lxml.Element
    LINK_ATTR_NAME = 'href'


class Link_link(ElementWithLink):
    # el is lxml.Element
    LINK_ATTR_NAME = 'href'


class IMG_link(ElementWithLink):
    # el is lxml.Element
    LINK_ATTR_NAME = 'src'


class Background_link(ElementWithLink):
    LINK_ATTR_NAME = 'background'


class CSS_link(ElementWithLink):

    # el is cssutils style property

    def __init__(self, el, updateme=None, encoding=None):
        ElementWithLink.__init__(self, el)
        self.updateme = updateme
        self.encoding = encoding
        #print __name__, "CSS_link", el, el.uri

    def get_link(self):
        return to_unicode(self.el.uri, self.encoding)

    def set_link(self, new):
        _old = self.el.uri
        if _old != new:
            logging.debug('Update link %s => %s ', _old, new)
            self.el.uri = new
            self._link_history.add(_old)
            if self.updateme:
                self.updateme.update()

    link = property(get_link, set_link)


def TAG_WRAPPER(attr):
    return ElementWithLink.make(attr)


CSS_WRAPPER = CSS_link
