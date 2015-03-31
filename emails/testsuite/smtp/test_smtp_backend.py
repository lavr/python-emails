# encoding: utf-8
from __future__ import unicode_literals
import os
import pytest
import emails

from emails.backend.smtp import SMTPBackend

TRAVIS_CI = os.environ.get('TRAVIS')

SAMPLE_MESSAGE = {'html': '<p>Test from python-emails',
                  'text': 'Test from python-emails',
                  'mail_from': 's@lavr.me',
                  'mail_to': 'sergei-nko@yandex.ru'}


def test_send_to_unknown_host():
    server = SMTPBackend(host='invalid-server.invalid-domain-42.com', port=2525)
    response = server.sendmail(to_addrs='s@lavr.me', from_addr='s@lavr.me', msg=emails.html(**SAMPLE_MESSAGE))
    server.close()
    assert response.status_code is None
    assert isinstance(response.error, IOError)
    assert not response.success
    print("response.error.errno=", response.error.errno)
    if not TRAVIS_CI:
        # IOError: [Errno 8] nodename nor servname provided, or not known
        assert response.error.errno == 8


def test_smtp_send_with_reconnect(smtp_servers):
    """
    Check SMTPBackend.sendmail reconnect
    """
    for tag, server in smtp_servers.items():
        print("-- test_smtp_reconnect: %s" % server)
        params = server.params
        params['fail_silently'] = True
        message = server.patch_message(emails.html(subject='reconnect test', **SAMPLE_MESSAGE))
        message.mail_from = server.from_email
        message.mail_to = server.to_email
        backend = message.smtp_pool[params]
        backend.get_client().sock.close()  # simulate disconnect
        response = message.send(smtp=params)
        assert response.success or response.status_code in (421, 451)  # gmail don't like test emails
        server.sleep()


def test_smtp_init_error():
    """
    Test error when ssl and tls arguments both set
    """
    with pytest.raises(ValueError):
        SMTPBackend(host='X', port=25, ssl=True, tls=True)


def test_smtp_empty_sendmail():
    response = SMTPBackend().sendmail(to_addrs=[], from_addr='a@b.com', msg='')
    assert not response

