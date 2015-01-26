# encoding: utf-8

import subprocess
import shlex
import time
import logging
import threading
import os
import os.path

import pytest


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

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
            logger.error('Started test smtp server "%s", pid: %s', CMD, self._process.pid)
            #print('Started test smtp server "{0}", pid: {1}'.format(CMD, self._process.pid))
            time.sleep(1)
        return self

    def stop(self):
        if self._process:
            logger.error('kill process...')
            self._process.terminate()


class TestLamsonSmtpServer:

    def __init__(self):
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        import lamsondebuggingsmtpinstance
        import lamsondebuggingsmtpinstance.config.settings
        self.lamsondir = os.path.dirname(lamsondebuggingsmtpinstance.__file__)
        settings = lamsondebuggingsmtpinstance.config.settings
        self.host = settings.receiver_config['host']
        self.port = settings.receiver_config['port']
        self.lock = threading.Lock()
        self._started = False


    def _lamson_command(self, lamson_params):
        r = subprocess.call("lamson {0}".format( lamson_params ), shell=True, cwd=self.lamsondir)
        print("_lamson_command '{0}' return code is {1}".format(lamson_params, r))
        return r

    def _start_lamson(self):
        if not self._started:
            self._stop_lamson() # just is case
            logger.debug('stop lamson...')
            return self._lamson_command('start -FORCE')

    def _stop_lamson(self):
        return self._lamson_command('stop')

    def get_server(self):
        self._start_lamson()
        time.sleep(1)
        return self

    def stop(self):
        if self._started:
            logger.debug('stop lamson...')
            self._start_lamson()


@pytest.fixture(scope="module")
def smtp_server(request):
    logger.debug('smtp_server...')
    try:
        import lamson
        ext_server = TestLamsonSmtpServer()
    except ImportError:
        ext_server = TestSmtpServer()
    def fin():
        print ("stopping ext_server")
        ext_server.stop()
    request.addfinalizer(fin)
    return ext_server.get_server() #host, ext_server.port)

@pytest.fixture(scope='module')
def django_email_backend(request):
    from django.conf import settings
    logger.debug('django_email_backend...')
    server = smtp_server(request)
    settings.configure(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
                        EMAIL_HOST=server.host, EMAIL_PORT=server.port)
    from django.core.mail import get_connection
    SETTINGS = {}
    return get_connection()

