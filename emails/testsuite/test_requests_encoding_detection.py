# encoding: utf-8

import requests

def test_encoding_detection():

    """
    Broken encoding detection in requests 1.2.3. 
    """
 
    url = 'http://lavr.github.io/python-emails/tests/requests/some-utf8-text.html'
    expected_content = u'我需要单间。' # Chinese is for example only. Any other encodings broken too.

    r =	requests.get(url)

    # Response.apparent_encoding is good
    assert r.apparent_encoding == 'utf-8'
    real_text = unicode(r.content, r.apparent_encoding)
    assert expected_content in real_text

    # but Response.text is broken
    # (the reason is: commit a0ae2e6)
    assert expected_content in r.text 

if __name__=="__main__":
   test_encoding_detection()
