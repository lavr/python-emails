# coding: utf-8
from __future__ import unicode_literals

import logging
import os

from emails.loader import cssinliner
import emails
from emails.compat import StringIO
from emails.template import JinjaTemplate
from emails.compat import NativeStringIO, to_bytes

from .helpers import TRAVIS_CI, HAS_INTERNET_CONNECTION, _email_data, common_email_data

try:
    from local_settings import SMTP_SERVER, SMTP_PORT, SMTP_SSL, SMTP_USER, SMTP_PASSWORD

    SMTP_DATA = {'host': SMTP_SERVER, 'port': SMTP_PORT,
                 'ssl': SMTP_SSL, 'user': SMTP_USER, 'password': SMTP_PASSWORD,
                 'debug': 0}
except ImportError:
    SMTP_DATA = None


def test_send1():
    URL = 'http://icdn.lenta.ru/images/2013/08/07/14/20130807143836932/top7_597745dde10ef36605a1239b0771ff62.jpg'
    data = _email_data()
    data['attachments'] = [emails.store.LazyHTTPFile(uri=URL), ]
    m = emails.html(**data)
    m.render(name='Полина')
    assert m.subject == 'Hello, Полина'
    if HAS_INTERNET_CONNECTION:
        r = m.send(smtp=SMTP_DATA)


def test_send_with_render():
    data = _email_data()
    m = emails.html(**data)
    m.render(name=u'Полина')
    assert m.subject == u'Hello, Полина'
    if HAS_INTERNET_CONNECTION:
        r = m.send(render={'name': u'Полина'}, smtp=SMTP_DATA)


def test_send2():
    data = _email_data()
    loader = emails.loader.HTTPLoader(filestore=emails.store.MemoryFileStore())
    URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html'
    loader.load_url(URL, css_inline=True, make_links_absolute=True, update_stylesheet=True)
    data['html'] = loader.html
    data['attachments'] = loader.attachments_dict
    loader.save_to_file('test_send2.html')
    m = emails.html(**data)
    m.render(name='Полина')

    if HAS_INTERNET_CONNECTION:
        r = m.send(smtp=SMTP_DATA)
        r = m.send(to='s.lavrinenko@gmail.com', smtp=SMTP_DATA)


def test_send_inline_images():
    data = _email_data()
    loader = emails.loader.HTTPLoader(filestore=emails.store.MemoryFileStore())
    URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html'
    loader.load_url(URL, css_inline=True, make_links_absolute=True, update_stylesheet=True)
    for img in loader.iter_image_links():
        link = img.link
        file = loader.filestore.by_uri(link, img.link_history)
        img.link = "cid:%s" % file.filename
    for file in loader.filestore:
        file.content_disposition = 'inline'
    data['html'] = loader.html
    data['attachments'] = loader.attachments_dict
    # loader.save_to_file('test_send_inline_images.html')
    m = emails.html(**data)
    m.render(name='Полина')

    if HAS_INTERNET_CONNECTION:
        r = m.send(smtp=SMTP_DATA)
        if r.status_code != 250:
            logging.error("Error sending email, response=%s" % r)
