# encoding: utf-8
from __future__ import unicode_literals, print_function

from emails.loader.helpers import (guess_charset, guess_text_charset, decode_text, guess_html_charset, RULES_U)


def test_re_rules():
    assert RULES_U.re_is_http_equiv.findall('http-equiv="Content-Type" content="text/html; charset=UTF-8"')


def test_guess_charset():
    assert guess_charset(headers={'content-type': 'text/html; charset=utf-8'}, html='') == 'utf-8'

    assert guess_charset(headers=None, html='<meta  charset="xxx-N"  >') == 'xxx-N'

    html = """<html><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />"""
    assert guess_charset(headers=None, html=html) == 'UTF-8'
    assert guess_text_charset(html, is_html=True) == 'UTF-8'
    assert guess_html_charset(html) == 'UTF-8'

    html = """Шла Саша по шоссе и сосала сушку"""
    assert guess_charset(headers=None, html=html.encode('utf-8')) == 'utf-8'


def test_decode_text():

    import encodings

    def norma_enc(enc):
        enc_ = encodings.normalize_encoding(enc.lower())
        enc_ = encodings._aliases.get(enc_) or enc_
        assert enc_
        return enc_

    assert decode_text(u'A')[0] == u'A'
    assert decode_text(b'A') == (u'A', 'ascii')

    for enc in ['utf-8', 'windows-1251', 'cp866']:
        t = u'Шла Саша по шоссе и сосала сушку. В огороде бузина, в Киеве дядька.'
        text, guessed_encoding = decode_text(t.encode(enc))
        print(text, norma_enc(guessed_encoding))
        assert (text, norma_enc(guessed_encoding)) == (t, norma_enc(enc))

        html = u"""<html><meta http-equiv="Content-Type" content="text/html; charset=%s" />""" % enc
        text, guessed_encoding = decode_text(html.encode('utf-8'), is_html=True)
        print(text, norma_enc(guessed_encoding))
        assert (text, norma_enc(guessed_encoding)) == (html, norma_enc(enc))
