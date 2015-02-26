# encoding: utf-8

import subprocess
import shlex
import time
import logging
import threading
import os
import os.path
import datetime
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


class SecureSMTPDServer(object):

    def __init__(self):
        self._cwd = os.path.join(os.path.dirname(__file__), 'contrib/local-smtpd')
        self._process = None
        self.host = 'localhost'
        self.user = 'A'
        self.password = 'B'
        self.argv = None

    def as_dict(self):
        r = {'host': self.host, 'port': self.port, 'fail_silently': False, 'debug': 1}
        argv = self.argv or []
        if 'ssl' in argv:
            r['ssl'] = True
        if 'auth' in argv:
            r.update({'user': self.user, 'password': self.password})
        return r

    def get_server(self, argv=None):
        if self._process is None:
            self.argv = argv or []
            if 'ssl' in self.argv:
                self.port = 25126
            elif 'auth' in self.argv:
                self.port = 25127
            else:
                self.port = 25125
            cmd = '/bin/sh ./run-smtpd.sh'.split(' ')
            if argv:
                cmd.extend(argv)
            self._process = subprocess.Popen(cmd, shell=False, cwd=self._cwd)
            logger.error('Started test smtp server "%s", pid: %s', cmd, self._process.pid)
            #print('Started test smtp server "{0}", pid: {1}'.format(CMD, self._process.pid))
            time.sleep(1)
        return self

    def stop(self):
        if self._process:
            logger.error('kill process...')
            self._process.terminate()
            time.sleep(1)


@pytest.fixture(scope="module")
def smtp_server(request):
    logger.debug('smtp_server...')
    ext_server = SecureSMTPDServer()
    def fin():
        print ("stopping ext_server")
        ext_server.stop()
    request.addfinalizer(fin)
    return ext_server.get_server()

@pytest.fixture(scope="module")
def smtp_server_with_auth(request):
    logger.debug('smtp_server with auth...')
    ext_server = SecureSMTPDServer()
    def fin():
        print ("stopping ext_server with auth")
        ext_server.stop()
    request.addfinalizer(fin)
    return ext_server.get_server(['auth'])


@pytest.fixture(scope="module")
def smtp_server_with_ssl(request):
    logger.debug('smtp_server with ssl...')
    ext_server = SecureSMTPDServer()
    def fin():
        print ("stopping ext_server with auth")
        ext_server.stop()
    request.addfinalizer(fin)
    return ext_server.get_server(['ssl'])


@pytest.fixture(scope='module')
def django_email_backend(request):
    from django.conf import settings
    logger.debug('django_email_backend...')
    settings.configure(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend',
                       EMAIL_FILE_PATH='tmp-emails')
    from django.core.mail import get_connection
    return get_connection()


class SMTPTestParams:

    subject_prefix = '[test-python-emails]'

    def __init__(self, from_email=None, to_email=None, defaults=None, **kw):
        params = {}
        params.update(defaults or {})
        params.update(kw)
        params['debug'] = 1
        params['timeout'] = 15
        self.params = params

        self.from_email = from_email
        self.to_email = to_email

    def patch_message(self, message):
        # Some SMTP requires from and to emails

        if self.from_email:
            message._mail_from = (message._mail_from[0], self.from_email)

        if self.to_email:
            message.mail_to = self.to_email

        # TODO: this code breaks template in subject; deal with this
        message.subject = " ".join([self.subject_prefix, datetime.datetime.now().strftime('%H:%M:%S'),
                                    message.subject])

    def __str__(self):
        return u'SMTPTestParams(host={0}, port={1}, user={2})'.format(self.params.get('host'),
                                                                      self.params.get('port'),
                                                                      self.params.get('user'))



@pytest.fixture(scope='module')
def smtp_servers(request):

    r = []

    """
    r.append(SMTPTestParams(from_email='drlavr@yandex.ru',
                         to_email='drlavr@yandex.ru',
                         fail_silently=False,
                         **{'host': 'mx.yandex.ru', 'port': 25, 'ssl': False}))

    r.append(SMTPTestParams(from_email='drlavr+togmail@yandex.ru',
                            to_email='s.lavrinenko@gmail.com',
                            fail_silently=False,
                            **{'host': 'gmail-smtp-in.l.google.com', 'port': 25, 'ssl': False}))


    r.append(SMTPTestParams(from_email='drlavr@yandex.ru',
                            to_email='s.lavrinenko@me.com',
                            fail_silently=False,
                            **{'host': 'mx3.mail.icloud.com', 'port': 25, 'ssl': False}))
    """

    r.append(SMTPTestParams(from_email='drlavr@yandex.ru',
                            to_email='lavr@outlook.com',
                            fail_silently=False,
                            **{'host': 'mx1.hotmail.com', 'port': 25, 'ssl': False}))

    try:
        from .local_smtp_settings import SMTP_SETTINGS_WITH_AUTH, FROM_EMAIL, TO_EMAIL
        r.append(SMTPTestParams(from_email=FROM_EMAIL,
                             to_email=TO_EMAIL,
                             fail_silently=False,
                             **SMTP_SETTINGS_WITH_AUTH))
    except ImportError:
        pass

    return r