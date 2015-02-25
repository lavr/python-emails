# encoding: utf-8
from __future__ import unicode_literals
import emails
import emails.message
import emails.django_


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
    django_email_backend.send_messages([emails.message.DjangoMessageProxy(msg), ])


def test_django_message(django_email_backend):

    message_params = {'html': '<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'subject': 'Test from python-emails'}
    msg = emails.django_.DjangoMessage(**message_params)
    assert not msg.recipients()

    TO = 'ivan@petrov.com'
    msg.send(mail_to=TO, set_mail_to=False)
    assert msg.recipients() == [TO, ]
    assert not msg.mail_to

    TO = 'x'+TO
    msg.send(mail_to=TO)
    assert msg.recipients() == [TO, ]
    assert msg.mail_to[0][1] == TO

    msg.send(context={'a':1})

