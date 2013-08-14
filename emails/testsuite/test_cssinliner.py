# coding: utf-8

import unittest

from emails.loader import cssinliner
from lxml import etree


def _do_inline_css(html, css, save_to_file=None, pretty_print=False):
    inliner = cssinliner.CSSInliner()
    inliner.DEBUG = True
    inliner.add_css(css)
    document = inliner.transform_html(html)
    r = etree.tostring(document, pretty_print=pretty_print)
    if save_to_file:
        open(save_to_file, 'w').write(r)
    return r


def test_unmergeable_css():

    HTML = "<a>b</a>"
    CSS = "a:visited {color: red;}"
    r = _do_inline_css(HTML, CSS, save_to_file='_result.html')
    print(r)


def test_commons():

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
