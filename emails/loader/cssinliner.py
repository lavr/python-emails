# -*- coding: utf-8 -*-
# adapted from https://github.com/kgn/cssutils/blob/master/examples/style.py
from __future__ import unicode_literals, print_function
from cssutils.css import CSSStyleSheet, CSSStyleDeclaration, CSSStyleRule
from cssutils import CSSParser
from lxml import etree
from lxml.builder import E
import logging

from emails.compat import to_unicode, string_types
import emails

# Workaround the missing python3-cssselect package
# If no system-installed cssselect library found, use one from our distribution
try:
    import cssselect
except ImportError:
    import sys, os.path
    my_packages = os.path.dirname(emails.packages.__file__)
    sys.path.insert(0, my_packages)
    import cssselect



class CSSInliner:

    NONVISUAL_TAGS = ['html', 'head', 'title', 'meta', 'link', 'script']

    DEBUG = False

    def __init__(self, base_url=None, css=None):

        self.stylesheet = CSSStyleSheet(href=base_url)
        self.base_url = base_url
        if css:
            self.add_css(css)

    def add_css(self, css, href=None):

        if isinstance(css, string_types):
            css = CSSParser().parseString(css, href=href)  # Распарсим файл

        for rule in css:
            """
            if rule.type == rule.STYLE_RULE:
                for property in rule.style:
                    if property.name.find('background')>=0:
                       _v = property.value
                       property.value = self.change_css_background( property.value, base_url = sheet.href )
                       #print '[after]', property.name,':', property.value
            """
            self.stylesheet.add(rule)

    def log(self, level, *msg):
        if self.DEBUG:
            print(('%s- %s' % (level * '\t ', ' '.join((to_unicode(m or '') for m in msg)))))

    def styleattribute(self, element):
            "returns css.CSSStyleDeclaration of inline styles, for html: @style"
            cssText = element.get('style')
            if cssText:
                try:
                    return CSSStyleDeclaration(cssText=cssText)
                except Exception as e:
                    # Sometimes here's error like "COLOR: ;"
                    logging.exception('Exception in styleattribute %s', cssText)
                    return None
            else:
                return None

    def getView(self, document, sheet, media='all', name=None, styleCallback=None):
        """
        document
            a DOM document, currently an lxml HTML document
        sheet
            a CSS StyleSheet object, currently cssutils sheet
        media: optional
            TODO: view for which media it should be
        name: optional
            TODO: names of sheets only
        styleCallback: optional
            should return css.CSSStyleDeclaration of inline styles, for html
            a style declaration for ``element@style``. Gets one parameter
            ``element`` which is the relevant DOMElement

        returns style view
            a dict of {DOMElement: css.CSSStyleDeclaration} for html
        """

        styleCallback = styleCallback or self.styleattribute

        _unmergable_rules = CSSStyleSheet()

        view = {}
        specificities = {}  # needed temporarily

        # TODO: filter rules simpler?, add @media
        rules = (rule for rule in sheet if rule.type == rule.STYLE_RULE)
        for rule in rules:
            for selector in rule.selectorList:
                self.log(0, 'SELECTOR', selector.selectorText)
                # TODO: make this a callback to be able to use other stuff than lxml
                try:
                    cssselector = CSSSelector(selector.selectorText)
                except (ExpressionError, NotImplementedError) as e:
                    _unmergable_rules.add(CSSStyleRule(selectorText=selector.selectorText,
                                                       style=rule.style))
                    continue

                matching = cssselector.evaluate(document)

                for element in matching:

                        if element.tag in self.NONVISUAL_TAGS:
                            continue

                        # add styles for all matching DOM elements
                        self.log(1, 'ELEMENT', id(element), element.text)

                        if element not in view:
                            # add initial empty style declatation
                            view[element] = CSSStyleDeclaration()
                            specificities[element] = {}

                            # and add inline @style if present
                            inlinestyle = styleCallback(element)
                            if inlinestyle:
                                for p in inlinestyle:
                                    # set inline style specificity
                                    view[element].setProperty(p)
                                    specificities[element][p.name] = (1, 0, 0, 0)

                        for p in rule.style:
                            # update style declaration
                            if p not in view[element]:
                                # setProperty needs a new Property object and
                                # MUST NOT reuse the existing Property
                                # which would be the same for all elements!
                                # see Issue #23
                                view[element].setProperty(p.name, p.value, p.priority)
                                specificities[element][p.name] = selector.specificity
                                self.log(2, view[element].getProperty('color'))

                            else:
                                self.log(2, view[element].getProperty('color'))
                                sameprio = (p.priority ==
                                            view[element].getPropertyPriority(p.name))
                                if not sameprio and bool(p.priority) or (
                                   sameprio and selector.specificity >=
                                        specificities[element][p.name]):
                                    # later, more specific or higher prio
                                    view[element].setProperty(p.name, p.value, p.priority)

        _unmergable_css = _unmergable_rules.cssText
        if _unmergable_css:
            e = etree.Element('style')
            # print __name__, _unmergable_css.__repr__()
            e.text = to_unicode(_unmergable_css, 'utf-8')
            body = document.find('body') or document
            body.insert(0, e)  # add <style> right into body

        return view

    def transform(self, html):

        if isinstance(html, string_types):
            html = etree.HTML(html, parser=etree.HTMLParser())

        view = self.getView(html, self.stylesheet)

        # - add style into @style attribute
        for element, style in list(view.items()):
            v = style.getCssText(separator='')
            element.set('style', v)

        return html

    transform_html = transform  # compatibility
