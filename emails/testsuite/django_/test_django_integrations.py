# encoding: utf-8
from __future__ import unicode_literals
import emails
import emails.message


def test_send_via_django_backend(django_email_backend):

    """
    Send email via django's email backend.
    `django_email_backend` defined in conftest.py
    """
    message_params = {'html': '<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'mail_to': 's.lavrinenko@gmail.com',
                      'subject': 'Test from python-emails'}
    msg = emails.html(**message_params)
    backend = django_email_backend
    print('... django_email_backend={0}'.format(backend))
    from django.core.mail import EmailMessage
    email = EmailMessage('Hello', 'Body goes here', 'from@example.com',
            ['to1@example.com', 'to2@example.com'], ['bcc@example.com'],
            headers = {'Reply-To': 'another@example.com'})
    backend.send_messages([email, ])


def test_django_message_proxy(django_email_backend):

    message_params = {'html': '<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'mail_to': 's.lavrinenko@gmail.com',
                      'subject': 'Test from python-emails'}
    msg = emails.html(**message_params)
    print "msg.mail_from=", msg.mail_from

    django_email_backend.send_messages([emails.message.DjangoMessageProxy(msg), ])
