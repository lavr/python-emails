# encoding: utf-8
from __future__ import unicode_literals

import emails
from emails.smtp import SMTPResponse, SMTPBackend
from emails.smtp.factory import ObjectFactory
import os

TRAVIS_CI = os.environ.get('TRAVIS')
HAS_INTERNET_CONNECTION = not TRAVIS_CI


def test_factory():

    class A:
        """ Sample class for testing """
        def __init__(self, a, b=None):
            self.a = a
            self.b = b

    factory = ObjectFactory(cls=A)

    obj1 = factory[{'a':1, 'b':2}]
    assert isinstance(obj1, A)
    assert obj1.a==1
    assert obj1.b==2

    obj2 = factory[{'a':1, 'b':2}]
    assert obj2 is obj1

    obj3 = factory[{'a':100 }]
    assert obj3 is not obj1



def test_exception_1():

    # IOError: [Errno 8] nodename nor servname provided, or not known
    server_params = { 'host': 'invalid-server.invalid-domain.xxx', 'port': 25 }
    sendmail_params = {'to_addrs': 's@lavr.me', 'from_addr': 's@lavr.me', 'msg': '...'}
    server = SMTPBackend(**server_params)
    response = server.sendmail(**sendmail_params)
    assert response.status_code is None
    assert response.error is not None
    assert isinstance(response.error, IOError)
    print("response.error.errno=", response.error.errno)
    if HAS_INTERNET_CONNECTION:
        assert response.error.errno==8


def test_exception_2(smtp_server):
    # Server disconnected
    host, port = smtp_server
    server_params = { 'host': host, 'port': port, 'debug':1 }

    message_params = {'html':'<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'mail_to': 'sergei-nko@yandex.ru',
                      'subject': 'Test from python-emails'}
    sendmail_params = {'to_addrs': 's@lavr.me',
                       'from_addr': 's@lavr.me',
                       'msg': emails.html(**message_params).as_string()}


    server = SMTPBackend(**server_params)
    server.open()
    server.connection.sock.close()  # simulate disconnect
    response = server.sendmail(**sendmail_params)
    print(response)



if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_factory()
    test_exception_1()