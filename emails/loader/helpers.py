# encoding: utf-8
from __future__ import unicode_literals
__all__ = ['guess_charset', 'fix_content_type']

import re
import cgi
import chardet
from emails.compat import to_unicode, is_py3, is_py2
import logging

# HTML page charset stuff

RE_CHARSET_U = re.compile(u"charset=\"?'?(.+)\"?'?", re.I + re.S + re.M)
RE_META_U = re.compile(u"<meta.*?http-equiv=\"?'?content-type\"?'?.*?>", re.I + re.S + re.M)
RE_INSIDE_META_U = re.compile(u"content=\"?'?([^\"'>]+)", re.I + re.S + re.M)

RE_CHARSET_B = re.compile(b"charset=\"?'?(.+)\"?'?", re.I + re.S + re.M)
RE_META_B = re.compile(b"<meta.*?http-equiv=\"?'?content-type\"?'?.*?>", re.I + re.S + re.M)
RE_INSIDE_META_B = re.compile(b"content=\"?'?([^\"'>]+)", re.I + re.S + re.M)


def fix_content_type(content_type, t='image'):
    if not content_type:
        return "%s/unknown" % t
    else:
        return content_type


def guess_charset(headers, html):

    # guess by http headers
    if headers:
        content_type = headers['content-type']
        if content_type:
            _, params = cgi.parse_header(content_type)
            r = params.get('charset', None)
            if r:
                return r

    # guess by html meta
    if isinstance(html, bytes):
        RE_META, RE_INSIDE_META, RE_CHARSET = RE_META_B, RE_INSIDE_META_B, RE_CHARSET_B
    else:
        # Should we guess encoding for unicode html ?
        RE_META, RE_INSIDE_META, RE_CHARSET = RE_META_U, RE_INSIDE_META_U, RE_CHARSET_U

    for s in RE_META.findall(html):
        for x in RE_INSIDE_META.findall(s):
            for charset in RE_CHARSET.findall(x):
                return to_unicode(charset)

    if isinstance(html, bytes):
        # guess by chardet
        return chardet.detect(html)['encoding']


