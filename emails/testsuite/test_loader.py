# encoding: utf-8

import emails
from emails.loader.stylesheets import StyledTagWrapper
import lxml

import os.path


def test_tagwithstyle():
    content = """<div style="background: url('http://yandex.ru/bg.png'); color: black;"/>"""
    tree = lxml.etree.HTML(content, parser=lxml.etree.HTMLParser())
    t = None
    for el in tree.iter():
        if el.get('style'):
            t = StyledTagWrapper(el)

    assert len(list(t.uri_properties())) == 1


def normalize_html(s):
    return "".join(s.split())

def test_insert_style():

    html = '<img src="1.png">'
    html =  """ <img src="1.png" style="background: url(2.png)"> <style>p {background: url(3.png)} </style> """
    tree = lxml.etree.HTML(html, parser=lxml.etree.HTMLParser())
    #print __name__, "test_insert_style step1: ", lxml.etree.tostring(tree, encoding='utf-8', method='html')
    emails.loader.helpers.add_body_stylesheet(tree,
                                    element_cls=lxml.etree.Element,
                                    tag="body",
                                    cssText="")

    #print __name__, "test_insert_style step2: ", lxml.etree.tostring(tree, encoding='utf-8', method='html')

    new_document = emails.loader.helpers.set_content_type_meta(tree, element_cls=lxml.etree.Element)
    if tree != new_document:
        # document may be updated here (i.e. html tag added)
        tree = new_document

    html = normalize_html(lxml.etree.tostring(tree, encoding='utf-8', method='html'))
    RESULT_HTML = normalize_html(u'<html><head><meta content="text/html; charset=utf-8" http-equiv="Content-Type"></head><body>' \
                 '<style></style><img src="1.png" style="background: url(2.png)"> '\
                 '<style>p {background: url(3.png)} </style> </body></html>')
    assert html==RESULT_HTML, "Invalid html expected: %s, got: %s" % (RESULT_HTML.__repr__(), html.__repr__())



def test_all_images():

    # Check if we load images from CSS:
    styles = emails.loader.stylesheets.PageStylesheets()
    styles.append(text="p {background: url(3.png);}")
    assert len(styles.uri_properties) == 1


    # Check if we load all images from html:
    HTML1 = """ <img src="1.png" style="background: url(2.png)"> <style>p {background: url(3.png)} </style> """
    loader = emails.loader.from_string(html=HTML1)
    # should be 3 image_link object
    assert len(list(loader.iter_image_links()))==3

    # should be 3 files in filestore
    files = set(loader.filestore.keys())
    assert len(files) == 3

    # Check if changing links affects result html:
    for obj in loader.iter_image_links():
        obj.link = "prefix_" + obj.link

    result_html = normalize_html( loader.html )
    VALID_RESULT = normalize_html("""<html><head><meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>"""\
                          """</head><body><style>p { background: url(prefix_3.png) }</style>"""\
                          """<img src="prefix_1.png" style="background: url(prefix_2.png)"/> </body></html>""")

    assert result_html == VALID_RESULT, "Invalid html expected: %s, got: %s" % (result_html.__repr__(), VALID_RESULT.__repr__())

def test_load_local_directory():
    ROOT = os.path.dirname(__file__)

    colordirect_html = "data/html_import/colordirect/html/left_sidebar.html"
    colordirect_loader = emails.loader.from_file(os.path.join(ROOT, colordirect_html))

    ALL_FILES = "bg_divider_top.png,bullet.png,img.png,img_deco_bottom.png,img_email.png,"\
                "bg_email.png,ico_lupa.png,img_deco.png".split(',')
    ALL_FILES = set(map(lambda n: "images/"+n, ALL_FILES))

    files = set(colordirect_loader.filestore.keys())

    not_attached = ALL_FILES - files

    return 0

    assert len(not_attached)==0, "Not attached files found: %s" % not_attached


    for fn in ( "data/html_import/colordirect/html/full_width.html",
                "data/html_import/oldornament/html/full_width.html"
            ):
        filename = os.path.join(ROOT, fn)
        print fn
        loader = emails.loader.from_file(filename)
        print loader.html


def test_load_sites():

    # Just load some sites.
    # Loader shouldn't thow exception

    URLs = [
        'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html',
        'https://github.com/lavr/python-emails',
        'http://cnn.com',
        'http://design.ru',
        'http://lenta.ru',
        'http://news.yandex.ru',
        'http://yahoo.com',
        'http://www.smashingmagazine.com/'
    ]

    for url in URLs[:1]:
        emails.loader.from_url(url)


def test_zip_load():
    ROOT = os.path.dirname(__file__)
    filename = os.path.join(ROOT, "data/html_import/oldornament.zip")
    loader = emails.loader.from_zip( open(filename, 'rb') )
    assert len(loader.filestore.keys())>=13
    #print len(loader.html)
    assert u"SET-3-old-ornament" in loader.html


def _do_inline_css(html, css, save_to_file=None, pretty_print=False):
    inliner = emails.loader.cssinliner.CSSInliner()
    inliner.DEBUG = True
    inliner.add_css(css)
    document = inliner.transform_html(html)
    r = lxml.etree.tostring(document, pretty_print=pretty_print)
    if save_to_file:
        open(save_to_file, 'w').write(r)
    return r


def test_unmergeable_css():

    HTML = "<a>b</a>"
    CSS = "a:visited {color: red;}"
    r = _do_inline_css(HTML, CSS, save_to_file='_result.html')
    print(r)


def test_commons_css_inline():

    tmpl = '''<html><head><title>style test</title></head><body>%s</body></html>'''

    HTML = tmpl % '''
            <h1>Style example 1</h1>
            <p>&lt;p></p>
            <p style="color: red;">&lt;p> with inline style: "color: red"</p>
            <p id="x" style="color: red;">p#x with inline style: "color: red"</p>
            <div>a &lt;div> green?</div>
            <div id="y">#y pink?</div>
        '''

    CSS = r'''
        * {
            margin: 0;
            }
        body {
            color: blue !important;
            font: normal 100% sans-serif;
        }
        p {
            c\olor: green;
            font-size: 2em;
        }
        p#x {
            color: black !important;
        }
        div {
            color: green;
            font-size: 1.5em;
            }
        #y {
            color: #f0f;
            }
        .cssutils {
            font: 1em "Lucida Console", monospace;
            border: 1px outset;
            padding: 5px;
        }
    '''

    VALID_RESULT = """<html>
  <head>
    <title>style test</title>
  </head>
  <body style="margin: 0;color: blue !important;font: normal 100% sans-serif">
            <h1 style="margin: 0">Style example 1</h1>
            <p style="margin: 0;color: green;font-size: 2em">&lt;p&gt;</p>
            <p style="color: red;margin: 0;font-size: 2em">&lt;p&gt; with inline style: "color: red"</p>
            <p id="x" style="color: black !important;margin: 0;font-size: 2em">p#x with inline style: "color: red"</p>
            <div style="margin: 0;color: green;font-size: 1.5em">a &lt;div&gt; green?</div>
            <div id="y" style="margin: 0;color: #f0f;font-size: 1.5em">#y pink?</div>
        </body>
</html>"""

    result = _do_inline_css(HTML, CSS, pretty_print=True)  # , save_to_file='_result.html')
    assert VALID_RESULT.strip() == result.strip()



if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_zip_load()
    test_insert_style()
    test_all_images()
    test_load_local_directory()
    test_load_sites()
    test_tagwithstyle()
    test_commons_css_inline()
    test_unmergeable_css()

