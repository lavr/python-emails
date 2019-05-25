# encoding: utf-8
import os

_from = os.environ.get('TEST_FROM_EMAIL') or 'python-emails@lavr.me'
_to = 'python.emails.test.2@yandex.ru'


def as_bool(value, default=False):
    if value is None:
        return default
    return value.lower() in ('1', 'yes', 'true', 'on')

DEFAULT_SERVERS = {
        'gmail.com-tls': dict(from_email=_from, to_email='s.lavrinenko+python-email-test@gmail.com',
                              host='alt1.gmail-smtp-in.l.google.com', port=25, tls=True),

        'mx.yandex.ru': dict(from_email=_from, to_email=_to,
                             host='mx.yandex.ru', port=25, tls=False),

        'outlook.com': dict(from_email=_from, to_email='lavr@outlook.com',
                            host='smtp-mail.outlook.com', port=587, tls=True),
    }


if os.environ.get('TEST_SMTP_HOST'):
    SERVERS = {
        'my': dict(
            host=os.environ.get('TEST_SMTP_HOST'),
            port=os.environ.get('TEST_SMTP_PORT') or 25,
            from_email=_from,
            to_email=os.environ.get('TEST_TO_EMAIL') or _to,
            tls=as_bool(os.environ.get('TEST_SMTP_TLS')),
            user=os.environ.get('TEST_SMTP_USER'),
            password=os.environ.get('TEST_SMTP_PASSWORD')
        )
    }
elif os.environ.get('TRAVIS'):
    pass
else:
    SERVERS = DEFAULT_SERVERS

