# encoding: utf-8
from __future__ import unicode_literals
import emails
import emails.message
from emails.django import DjangoMessage


def test_django_message_proxy(django_email_backend):

    """
    Send message via django email backend.
    `django_email_backend` defined in conftest.py
    """

    message_params = {'html': '<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'mail_to': 's.lavrinenko@gmail.com',
                      'subject': 'Test from python-emails'}
    msg = emails.html(**message_params)
    django_email_backend.send_messages([emails.message.DjangoMessageProxy(msg), ])


def test_django_message_send(django_email_backend):

    message_params = {'html': '<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'subject': 'Test from python-emails'}
    msg = DjangoMessage(**message_params)
    assert not msg.recipients()

    TO = 'ivan@petrov.com'
    msg.send(mail_to=TO, set_mail_to=False)
    assert msg.recipients() == [TO, ]
    assert not msg.mail_to

    TO = 'x'+TO
    msg.send(mail_to=TO)
    assert msg.recipients() == [TO, ]
    assert msg.mail_to[0][1] == TO

    msg.send(context={'a': 1})


def test_django_message_commons():

    mp = {'html': '<p>Test from python-emails',
          'mail_from': 's@lavr.me',
          'mail_to': 'jsmith@company.tld',
          'charset': 'XXX-Y'}
    msg = DjangoMessage(**mp)

    assert msg.encoding == mp['charset']

    # --- check recipients()

    assert msg.recipients() == [mp['mail_to'], ]

    msg._set_emails(mail_to='A', set_mail_to=False)
    assert msg.recipients() == ['A', ]
    assert msg.mail_to[0][1] == mp['mail_to']

    msg._set_emails(mail_to='a@a.com', set_mail_to=True)
    assert msg.recipients() == ['a@a.com', ]
    assert msg.mail_to[0][1] == 'a@a.com'

    # --- check from_email

    assert msg.from_email == mp['mail_from']

    msg._set_emails(mail_from='b@b.com', set_mail_from=False)
    assert msg.from_email == 'b@b.com'
    assert msg.mail_from[1] == mp['mail_from']

    msg._set_emails(mail_from='c@c.com', set_mail_from=True)
    assert msg.from_email == 'c@c.com'
    assert msg.mail_from[1] == 'c@c.com'