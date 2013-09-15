import requests
print requests.__file__
from requests.packages import charade

def test_charade_encoding():
    url = 'https://github.yandex-team.ru/pages/lavrinenko/letters/yandex-mail/MAILPROTO-847/admin_letter.html'
    r =	requests.get(url)
    assert (r.encoding is None) or r.encoding=='utf-8'
    assert r.apparent_encoding == 'utf-8'
    raw = r.content
    assert charade.detect(raw)['encoding']=='utf-8'
    print r.text

if __name__=="__main__":
   test_charade_encoding()
