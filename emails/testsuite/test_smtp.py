# encoding: utf-8
import emails
from emails.smtp import SMTPConnectionPool, SMTPResponse, SMTPSender

def test_exceptions():

    # IOError: [Errno 8] nodename nor servname provided, or not known
    server_params = { 'host': 'invalid-server.invalid-domain.xxx', 'port': 25 }
    sendmail_params = {'to_addrs': 's@lavr.me', 'from_addr': 's@lavr.me', 'msg': '...'}
    server = SMTPSender(**server_params)
    response = server.sendmail(**sendmail_params)
    assert response.status_code is None
    assert response.error is not None
    assert isinstance(response.error, IOError)
    assert response.error.errno==8


    # Server disconnected
    message_params = {'html':'<p>Test from python-emails',
                      'mail_from': 's@lavr.me',
                      'mail_to': 'sergei-nko@yandex.ru',
                      'subject': 'Test from python-emails'}
    server_params = { 'host': 'mx.yandex.ru', 'port': 25, 'debug':1 }
    sendmail_params = {'to_addrs': 'sergei-nko@yandex.ru',
                       'from_addr': 's@lavr.me',
                       'msg': emails.html(**message_params).as_string()}
    server = SMTPSender(**server_params)
    server._connect()
    server.smtpclient.sock.close()  # simulate disconnect
    response = server.sendmail(**sendmail_params)
    print response


if __name__=="__main__":
    test_exceptions()