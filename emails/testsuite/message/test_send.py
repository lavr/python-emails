# coding: utf-8
from __future__ import unicode_literals

import emails
import emails.loader

from .helpers import HAS_INTERNET_CONNECTION, common_email_data

def test_send_attachment(smtp_servers):
    """
    Test email with attachment
    """
    URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/images/gallery.png'
    data = common_email_data(subject='Single attachment', attachments=[emails.store.LazyHTTPFile(uri=URL), ])
    m = emails.html(**data)
    if HAS_INTERNET_CONNECTION:
        for d in smtp_servers:
            d.patch_message(m)
            r = m.send(smtp=d.params)


def test_send_with_render(smtp_servers):
    data = common_email_data(subject='Render with name=John')
    m = emails.html(**data)
    if HAS_INTERNET_CONNECTION:
        for d in smtp_servers:
            d.patch_message(m)
            r = m.send(render={'name': u'John'}, smtp=d.params)


def test_send_with_inline_images(smtp_servers):
    url = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html'
    data = common_email_data(subject='Sample html with inline images')
    del data['html']
    m = emails.loader.from_url(url=url, message_params=data, images_inline=True)
    if HAS_INTERNET_CONNECTION:
        for d in smtp_servers:
            d.patch_message(m)
            r = m.send(smtp=d.params)
