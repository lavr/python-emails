# encoding: utf-8
from __future__ import unicode_literals
from emails.transformer import Transformer
import emails.loader


def test_image_apply():

    pairs = [
        ("""<div style="background: url(3.png);"></div>""",
         """<div style="background: url(A/3.png)"></div>"""),

        ("""<img src="4.png">""",
         """<img src="A/4.png">"""),

        ("""<table background="5.png">""",
         """<table background="A/5.png">""")
    ]

    def func(uri, **kw):
        return "A/"+uri

    for before, after in pairs:
        t = Transformer(html=before)
        t.apply_to_images(func)
        assert after in t.to_string()



def test_link_apply():

    pairs = [
        ("""<a href="1"></a>""",
         """<a href="A/1"></a>"""),
    ]

    def func(uri, **kw):
        return "A/"+uri

    for before, after in pairs:
        t = Transformer(html=before)
        t.apply_to_links(func)
        assert after in t.to_string()


def test_tag_attribute():


    m1 = emails.loader.from_string(html="""<img src="1.jpg">""")
    assert len(m1.attachments.keys()) == 1
    assert m1.attachments['1.jpg'].content_disposition != "inline"

    m2 = emails.loader.from_string(html="""<img src="1.jpg" data-emails="ignore">""")
    assert len(m2.attachments.keys()) == 0

    m3 = emails.loader.from_string(html="""<img src="1.jpg" data-emails="inline">""")
    assert len(m3.attachments.keys()) == 1
    assert m3.attachments['1.jpg'].content_disposition == "inline"