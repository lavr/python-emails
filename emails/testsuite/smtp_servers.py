# encoding: utf-8

_from = 'python-emails@lavr.me'

_mailtrap = dict(user='324263f0d84f52b2a', password='#e:lZdnZ5iUmJOcm2Wca2c=',
                 host='mailtrap.io', to_email='324263f0d84f52b2a@mailtrap.io')

SERVERS = {
    'gmail.com-tls': dict(from_email=_from, to_email='s.lavrinenko@gmail.com',
                          host='alt1.gmail-smtp-in.l.google.com', port=25, tls=True),

    'mx.yandex.ru': dict(from_email=_from, to_email='python.emails.test.2@yandex.ru',
                         host='mx.yandex.ru', port=25),

    #'mailtrap.io': dict(from_email=_from, port=25, **_mailtrap),
    #'mailtrap.io-tls': dict(from_email=_from, tls=True, port=465, **_mailtrap),
    # mailtrap disabled because of timeouts on Travis

    'outlook.com': dict(from_email=_from, to_email='lavr@outlook.com', host='mx1.hotmail.com'),

    #'me.com': dict(from_email=_from, to_email='s.lavrinenko@me.com', host='mx3.mail.icloud.com'),
    # icloud.com disabled because of timeouts on Travis
}
