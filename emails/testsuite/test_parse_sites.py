# encoding: utf-8

import emails


def _parse_one_page(url):
    loader = emails.loader.HTTPLoader(filestore=emails.store.MemoryFileStore())
    loader.load_url(url=url, css_inline=True, make_links_absolute=True)
    loader.save_to_file('parsed_page.html')


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
    test_load_sites()
