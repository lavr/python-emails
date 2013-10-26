# encoding: utf-8
import pytest
import requests

@pytest.mark.xfail
def test_encoding_detection():

    """
    Broken encoding detection in requests 1.2.3. 
    I'm failed to explain this bug importance to requests's team: 
    https://github.com/kennethreitz/requests/issues/1604 
    """
 
    url = 'http://lavr.github.io/python-emails/tests/requests/some-utf8-text.html'
    expected_content = u'我需要单间。' # Chinese is for example only. Any other non-european encodings broken too.

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
