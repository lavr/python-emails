# encoding: utf-8
from __future__ import print_function
from emails.transformer import HTMLParser


def test_parser_inputs():

    def _cleaned_body(s):
        for el in ('html', 'body', 'head'):
            s = s.replace('<%s>' % el, '').replace('</%s>' % el, '').replace('<%s/>' % el, '')
        return s

    # This is a fixation of de-facto rendering results

    for html, result in (
            ("<html><!-- comment -->", "<!-- comment -->"),
            ("<a href='[]&'>_</a>", '<a href="[]&amp;">_</a>'),
            ('<p>a\r\n', '<p>a</p>')
    ):
        r = HTMLParser(html=html).to_string()
        print("html=", html.__repr__(), "result=", r.__repr__(), sep='')
        assert _cleaned_body(r) == result


def test_breaking_title():
    # xml-styled <title/> breaks html rendering, we should remove it (#43)
    assert '<title/>' not in HTMLParser(html="<title></title>").to_string()
