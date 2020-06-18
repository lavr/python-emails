# coding: utf-8
from __future__ import unicode_literals
import time
import random
import emails
import emails.loader
from emails.backend.smtp import SMTPBackend

from .helpers import common_email_data
from emails.testsuite.smtp_servers import get_servers


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


def test_send_letters():

    for m, render in get_letters():
        for tag, server in get_servers():
            server.patch_message(m)
            print(tag, server.params)
            response = m.send(smtp=server.params, render=render)
            print(server.params)
            assert response.success or response.status_code in (421, 451)  # gmail not always like test emails
            server.sleep()


def test_send_with_context_manager():
    for _, server in get_servers():
        b = SMTPBackend(**server.params)
        with b as backend:
            for n in range(2):
                data = common_email_data(subject='context manager {0}'.format(n))
                message = emails.html(**data)
                message = server.patch_message(message)
                response = message.send(smtp=backend)
                assert response.success or response.status_code in (421, 451), 'error sending to {0}'.format(server.params)  # gmail not always like test emails
        assert b._client is None
