# encoding: utf-8
from __future__ import unicode_literals
__all__ = ['guess_charset', 'fix_content_type']

import re
import cgi
import chardet
from emails.compat import to_unicode, to_bytes

import logging

# HTML page charset stuff

RE_CHARSET = re.compile(b"charset=\"?'?(.+)\"?'?", re.I + re.S + re.M)
RE_META = re.compile(b"<meta.*?http-equiv=\"?'?content-type\"?'?.*?>", re.I + re.S + re.M)
RE_INSIDE_META = re.compile(b"content=\"?'?([^\"'>]+)", re.I + re.S + re.M)


def fix_content_type(content_type, t='image'):
    if (not content_type):
        return "%s/unknown" % t
    else:
        return content_type


def guess_charset(headers, html):

    # guess by http headers
    if headers:
        #print(__name__, "guess_charset has headers", headers)
        content_type = headers['content-type']
        if content_type:
            _, params = cgi.parse_header(content_type)
            r = params.get('charset', None)
            if r:
                return r

    # guess by html meta
    #print(__name__, "guess_charset html=", html[:1024])
    for s in RE_META.findall(html):
        for x in RE_INSIDE_META.findall(s):
            for charset in RE_CHARSET.findall(x):
                return to_unicode(charset)

    # guess by chardet
    return chardet.detect(html)['encoding']


def set_content_type_meta(document, element_cls, content_type="text/html", charset="utf-8"):

    if document is None:
        document = element_cls('html')

    if document.tag!='html':
        html = element_cls('html')
        html.insert(0, document)
        document = html
    else:
        html = document

    head = document.find('head')
    if head is None:
        head = element_cls('head')
        html.insert(0, head)

    content_type_meta = None

    for meta in head.find('meta') or []:
        http_equiv = meta.get('http-equiv', None)
        if http_equiv and (http_equiv.lower() == 'content_type'):
            content_type_meta = meta
            break

    if content_type_meta is None:
        content_type_meta = element_cls('meta')
        head.append(content_type_meta)

    content_type_meta.set('content', '%s; charset=%s' % (content_type, charset))
    content_type_meta.set('http-equiv', "Content-Type")

    return document


def add_body_stylesheet(document, element_cls, cssText, tag="body"):

    style = element_cls('style')
    style.text = cssText

    body = document.find(tag)
    if body is None:
        body = document

    body.insert(0, style)

    return style
