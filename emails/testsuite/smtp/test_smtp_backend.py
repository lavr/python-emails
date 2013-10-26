# encoding: utf-8
from __future__ import unicode_literals

import emails
from emails.smtp import SMTPResponse, SMTPBackend
import os

TRAVIS_CI = os.environ.get('TRAVIS')
HAS_INTERNET_CONNECTION = not TRAVIS_CI


def test_send_to_unknow_host():
    server = SMTPBackend(host='invalid-server.invalid-domain.com', port=25)
    response = server.sendmail(to_addrs='s@lavr.me', from_addr='s@lavr.me',  msg='...')
    assert response.status_code is None
    assert response.error is not None
    assert isinstance(response.error, IOError)
    print("response.error.errno=", response.error.errno)
    if HAS_INTERNET_CONNECTION:
        # IOError: [Errno 8] nodename nor servname provided, or not known
        assert response.error.errno==8


def test_smtp_reconnect(smtp_server):

    # Simulate server disconnection
    # Check that SMTPBackend will reconnect

    message_params = {'html':'<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'mail_to': 'sergei-nko@yandex.ru',
                      'subject': 'Test from python-emails'}

    server = SMTPBackend(host=smtp_server.host, port=smtp_server.port, debug=1)
    server.open()
    server.connection.sock.close()  # simulate disconnect
    response = server.sendmail(to_addrs='s@lavr.me',
                               from_addr='s@lavr.me',
                               msg=emails.html(**message_params).as_string())
    print(response)



if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_send_to_unknow_host()
    test_smtp_reconnect()