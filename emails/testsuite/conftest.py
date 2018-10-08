# encoding: utf-8
import logging
import datetime
import pytest
import base64
import time
import random
import sys
import platform

from emails.compat import to_native, is_py3, to_unicode

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

import cssutils
cssutils.log.setLevel(logging.FATAL)

@pytest.fixture(scope='module')
def django_email_backend(request):
    from django.conf import settings
    logger.debug('django_email_backend...')
    settings.configure(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend',
                       EMAIL_FILE_PATH='tmp-emails')
    from django.core.mail import get_connection
    return get_connection()


def obsfucate(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc))


def deobsfucate(key, enc):
    dec = []
    key = to_native(key)
    enc = base64.urlsafe_b64decode(enc)
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        if is_py3:
            c1 = enc[i]
        else:
            c1 = ord(enc[i])
        dec_c = chr((256 + c1 - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)
    assert 0


class SMTPTestParams:

    subject_prefix = '[python-emails]'

    def __init__(self, from_email=None, to_email=None, defaults=None, **kw):
        params = {'fail_silently': True, 'debug': 1, 'timeout': 25}
        params.update(defaults or {})
        params.update(kw)
        self.params = params
        pwd = params.get('password')
        if pwd and pwd.startswith('#e:'):
            user = params.get('user')
            params['password'] = deobsfucate(user, pwd[3:])
        self.from_email = from_email
        self.to_email = to_email

    def patch_message(self, message):
        """
        Some SMTP requires from and to emails
        """

        if self.from_email:
            message.mail_from = (message.mail_from[0], self.from_email)

        if self.to_email:
            message.mail_to = self.to_email

        # TODO: this code breaks template in subject; fix it
        if not to_unicode(message.subject).startswith(self.subject_prefix) :
            message.subject = " ".join([self.subject_prefix, message.subject,
                                        'py%s' % sys.version[:3]])

        message._headers['X-Test-Date'] = datetime.datetime.utcnow().isoformat()
        message._headers['X-Python-Version'] = "%s/%s" % (platform.python_version(), platform.platform())

        return message

    def __str__(self):
        return u'SMTPTestParams({user}@{host}:{port})'.format(host=self.params.get('host'),
                                                              port=self.params.get('port'),
                                                              user=self.params.get('user', ''))

    def sleep(self):
        if 'mailtrap' in self.params.get('host', ''):
            t = 2 + random.randint(0, 2)
        else:
            t = 0.5
        time.sleep(t)


@pytest.fixture(scope='module')
def smtp_servers(request):

    try:
        from .local_smtp_severs import SERVERS
    except ImportError:
        from .smtp_servers import SERVERS

    return dict([(k, SMTPTestParams(**v)) for k, v in SERVERS.items()])
