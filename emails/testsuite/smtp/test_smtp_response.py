# encoding: utf-8
from emails.backend.response import SMTPResponse


def test_smtp_response_defaults():
    r = SMTPResponse()
    assert r.status_code is None
    assert r.status_text is None
    assert r.refused_recipients == {}
    assert r.esmtp_opts is None
    assert r.rcpt_options is None
    assert not r.success
    assert r.error is None


def test_smtp_response_set_status():
    r = SMTPResponse()
    r.set_status('mail', 250, 'OK')
    assert r.status_code == 250
    assert r.status_text == 'OK'
    assert r.last_command == 'mail'
    assert len(r.responses) == 1


def test_smtp_response_success():
    r = SMTPResponse()
    r.set_status('data', 250, 'OK')
    assert not r.success  # _finished is False
    r._finished = True
    assert r.success


def test_smtp_response_refused_recipients():
    r = SMTPResponse()
    r.refused_recipients = {}
    r.refused_recipients['bad@example.com'] = (550, b'User unknown')
    assert 'bad@example.com' in r.refused_recipients
    assert r.refused_recipients['bad@example.com'] == (550, b'User unknown')


def test_smtp_response_exception():
    exc = Exception('connection failed')
    r = SMTPResponse(exception=exc)
    assert r.error is exc
    assert not r.success
