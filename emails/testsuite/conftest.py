# encoding: utf-8

import pytest
import subprocess
import shlex
import time
import logging
import threading

TEST_SMTP_PORT = 25125

class TestSmtpServer:

    def __init__(self, host=None, port=None):
        self._process = None
        self.host = host or 'localhost'
        self.port = port or TEST_SMTP_PORT
        self.lock = threading.Lock()

    def get_server(self):

        if self._process is None:
            CMD = 'python -m smtpd -d -n -c DebuggingServer %s:%s' % (self.host, self.port)
            self._process = subprocess.Popen(shlex.split(CMD), shell=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            logging.error('Started test smtp server "%s", pid: %s', CMD, self._process.pid)
            #print('Started test smtp server "{0}", pid: {1}'.format(CMD, self._process.pid))
            time.sleep(1)
        return (self.host, self.port)

    def stop(self):
        if self._process:
            logging.error('kill process...')
            self._process.terminate()

@pytest.fixture(scope="module")
def smtp_server(request):
    logging.debug('smtp_server...')
    ext_server = TestSmtpServer()
    time.sleep(1)
    def fin():
        print ("stopping ext_server")
        ext_server.stop()
    request.addfinalizer(fin)
    return ext_server.get_server() #host, ext_server.port)

@pytest.fixture(scope='module')
def django_email_backend(request):
    from django.conf import settings
    logging.debug('django_email_backend...')
    host, port = smtp_server(request)
    settings.configure(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
                        EMAIL_HOST=host, EMAIL_PORT=port)
    from django.core.mail import get_connection
    SETTINGS = {}
    return get_connection()

