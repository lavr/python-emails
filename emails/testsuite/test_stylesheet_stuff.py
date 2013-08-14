# encoding: utf-8

import emails
from emails.loader.stylesheets import StyledTagWrapper
import lxml


def test_tagwithstyle():
    content = """<div style="background: url('http://yandex.ru/bg.png'); color: black;"/>"""
    tree = lxml.etree.HTML(content, parser=lxml.etree.HTMLParser())
    t = None
    for el in tree.iter():
        if el.get('style'):
            t = StyledTagWrapper(el)

    assert len(list(t.uri_properties())) == 1


if __name__ == '__main__':
    test_tagwithstyle()
