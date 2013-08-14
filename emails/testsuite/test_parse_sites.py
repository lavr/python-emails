# encoding: utf-8

import emails
import os.path


def _parse_one_page(url):
    loader = emails.loader.HTTPLoader(filestore=emails.store.MemoryFileStore())
    loader.load_url(url=url, css_inline=True, make_links_absolute=True)
    loader.save_to_file('parsed_page.html')


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
        _parse_one_page(url)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_load_local_directory()
    #test_load_sites()
