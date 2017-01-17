# encoding: utf-8
from __future__ import unicode_literals
import os.path
import emails.loader
from emails.loader.local_store import FileSystemLoader, BaseLoader
from emails.template import JinjaTemplate, StringTemplate, MakoTemplate
from emails.transformer import Transformer, LocalPremailer, BaseTransformer, HTMLParser


def test_image_apply():

    pairs = [
        ("""<div style="background: url(3.png);">x</div>""",
         """<div style="background: url(A/3.png)">x</div>"""),

        ("""<img src="4.png"/>""",
         """<img src="A/4.png"/>"""),

        ("""<table background="5.png"/>""",
         """<table background="A/5.png"/>""")
    ]

    def func(uri, **kw):
        return "A/"+uri

    for before, after in pairs:
        t = Transformer(html=before)
        t.apply_to_images(func)
        assert after in t.to_string()


def test_entity_13():
    assert Transformer(html="<div>x\r\n</div>").to_string() == '<html><head/><body><div>x\n</div></body></html>'


def test_link_apply():

    pairs = [
        ("""<a href="1">_</a>""",
         """<a href="A/1">_</a>"""),
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


ROOT = os.path.dirname(__file__)

def test_local_premailer():
    local_loader = FileSystemLoader(os.path.join(ROOT, "data/premailer_load"))
    lp = LocalPremailer(html='<link href="style.css" rel="stylesheet" /><a href="#">', local_loader=local_loader)
    assert '<a href="#" style="color:#000">' in lp.transform()


def test_add_content_type_meta():
    t = Transformer(html="<div></div>")
    t.premailer.transform()
    assert type(t.html) == type(t.to_string())
    t.add_content_type_meta(content_type="text/html", charset="utf-16")
    assert 'content="text/html; charset=utf-16"' in t.to_string()


def test_image_inline():

    class SimpleLoader(BaseLoader):
        def __init__(self, data):
            self.__data = data
        def list_files(self):
            return self.__data.keys()
        def get_file(self, name):
            return self.__data.get(name, None), name

    t = Transformer(html="<div><img src='a.gif'></div>", local_loader=SimpleLoader(data={'a.gif': 'xxx'}))
    t.load_and_transform()

    t.attachment_store['a.gif'].content_disposition = 'inline'
    t.synchronize_inline_images()
    t.save()
    assert "cid:a.gif" in t.html

    t.attachment_store['a.gif'].content_disposition = None
    t.synchronize_inline_images()
    t.save()
    assert '<img src="a.gif"' in t.html

    # test inline image in css
    t = Transformer(html="<div style='background:url(a.gif);'></div>", local_loader=SimpleLoader(data={'a.gif': 'xxx'}))
    t.load_and_transform()
    t.attachment_store['a.gif'].content_disposition = 'inline'
    t.synchronize_inline_images()
    t.save()
    assert "url(cid:a.gif)" in t.html



def test_absolute_url():
    t = Transformer(html="", base_url="https://host1.tld/a/b")
    assert t.get_absolute_url('c.gif') == 'https://host1.tld/a/b/c.gif'
    assert t.get_absolute_url('/c.gif') == 'https://host1.tld/c.gif'
    assert t.get_absolute_url('//host2.tld/x/y.png') == 'https://host2.tld/x/y.png'


def test_html_parser_with_templates():
    for _, html in (
            (JinjaTemplate, '{{ name }} <a href="{{ link }}">_</a>'),
            (StringTemplate, '${name} <a href="${link}">_</a>'),
            (MakoTemplate, '${name} <a href="${link}">_</a>')
    ):
        # Test that html parser doesn't break template code
        t = HTMLParser(html=html, method='html')
        assert html in t.to_string()


def test_template_transformer():
    """
    Test that transformer works with templates
    """
    for template_cls, tmpl in (
            (JinjaTemplate, '{{ name }} <a href="{{ link }}">_</a>'),
            (StringTemplate, '${name} <a href="${link}">_</a>'),
            (MakoTemplate, '${name} <a href="${link}">_</a>')
    ):
        m = emails.Message(html=template_cls(tmpl))
        m.transformer.premailer.transform()
        m.transformer.save()
        m.render(name='NAME', link='LINK')
        assert '<html>' in m.html_body
        assert 'NAME' in m.html_body
        assert '<a href="LINK">_</a>' in m.html_body
