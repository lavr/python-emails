# coding: utf-8
from __future__ import unicode_literals
import time
import random
import emails
import emails.loader

from .helpers import common_email_data


def get_letters():

    # Test email with attachment
    URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/images/gallery.png'
    data = common_email_data(subject='Single attachment', attachments=[emails.store.LazyHTTPFile(uri=URL), ])
    yield emails.html(**data), None

    # Email with render
    yield emails.html(**common_email_data(subject='Render with name=John')), {'name': u'John'}

    # Email with several inline images
    url = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html'
    data = common_email_data(subject='Sample html with inline images')
    del data['html']
    yield emails.loader.from_url(url=url, message_params=data, images_inline=True), None


def test_send_letters(smtp_servers):

    for m, render in get_letters():
        for tag, server in smtp_servers.items():
            server.patch_message(m)
            response = m.send(smtp=server.params, render=render)
            assert response.success or response.status_code in (421, 451)  # gmail not always like test emails
            server.sleep()
