# encoding: utf-8

import pytest
import subprocess
import shlex
import time
import logging

TEST_SMTP_PORT = 25125


class TestSmtpServer:

    def __init__(self, host=None, port=None):
        self._process = None
        self.host = host or 'localhost'
        self.port = port or TEST_SMTP_PORT

    def get_server(self):
        with threading.RLock:
            if self._process is None:
                CMD = 'python -m smtpd -n -c DebuggingServer %s:%s' % (self.host, self.port)
                self._process = subprocess.Popen(shlex.split(CMD))
                logging.debug('Started test smtp server "%s", pid: %s', CMD, self._process.pid)
            return (self.hosts, self.port)

    def stop(self):
        if self._process:
            self._process.kill()


@pytest.fixture(scope="module")
def smtp_server(request):
    ext_server = TestSmtpServer()
    def fin():
        print ("stopping ext_server")
        ext_server.stop()
    request.addfinalizer(fin)
    return (ext_server.host, ext_server.port)

@pytest.fixture(scope='module')
def django_email_backend(request):
    from django.core.mail import get_connection
    return get_connection()

