# encoding: utf-8
from __future__ import unicode_literals

import emails
from emails.smtp import SMTPConnectionFactory, SMTPResponse, SMTPBackend
import os
import time

TRAVIS_CI = os.environ.get('TRAVIS')
HAS_INTERNET_CONNECTION = not TRAVIS_CI


def test_send_via_django_backend(django_email_backend):

    print('test_send_via_django_backend...')
    message_params = {'html':'<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'mail_to': 'sergei-nko@yandex.ru',
                      'subject': 'Test from python-emails'}
    msg = emails.html(**message_params)
    backend = django_email_backend
    print('... django_email_backend={0}'.format(backend))

    from django.core.mail import EmailMessage

    email = EmailMessage('Hello', 'Body goes here', 'from@example.com',
            ['to1@example.com', 'to2@example.com'], ['bcc@example.com'],
            headers = {'Reply-To': 'another@example.com'})

    backend.send_messages([email, ])

    print("backend=%s", backend)

