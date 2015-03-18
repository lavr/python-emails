# encoding: utf-8
from __future__ import print_function
from emails.transformer import HTMLParser


def print_parser_methods():
    html = '<a href="{{ x }}">_</a> \r\n'
    for method in ['xml', 'html']:
        for output_method in ['xml', 'html']:
            print("method=", method, " output_method=", output_method, sep='')
            print(HTMLParser(html=html, method=method, output_method=output_method).to_string())
    print(HTMLParser('<a href="a&b">_</a>', method="html", output_method="html").to_string())
    print(HTMLParser('<html><!-- comment -->', method="html", output_method="html").to_string())


def test_parser_inputs():

    def _cleaned_body(s):
        for el in ('html', 'body'):
            s = s.replace('<%s>' % el, '').replace('</%s>' % el, '')
        return s

    for html, result in (
            ("<html><!-- comment -->", "<!-- comment -->"),
            ("<a href='[]&'>_</a>", '<a href="[]&amp;">_</a>'),
            ('<p>a\r\n', '<p>a</p>')
    ):
        r = HTMLParser(html=html).to_string()
        print("html=", html.__repr__(), "result=", r.__repr__(), sep='')
        assert _cleaned_body(r) == result