# encoding: utf-8
import os
import platform
import datetime
import random
import time
from emails.compat import to_unicode

DEFAULT_FROM = os.environ.get('SMTP_TEST_FROM_EMAIL') or 'python-emails@lavr.me'
SUBJECT_SUFFIX = os.environ.get('SMTP_TEST_SUBJECT_SUFFIX')


def as_bool(value, default=False):
    if value is None:
        return default
    return value.lower() in ('1', 'yes', 'true', 'on')


"""
Take environment variables if exists and send test letter

SMTP_TEST_SETS=GMAIL,OUTLOOK,YAMAIL

SMTP_TEST_GMAIL_TO=somebody@gmail.com
SMTP_TEST_GMAIL_USER=myuser
SMTP_TEST_GMAIL_PASSWORD=mypassword
SMTP_TEST_GMAIL_WITH_TLS=true
SMTP_TEST_GMAIL_WITHOUT_TLS=false
SMTP_TEST_GMAIL_HOST=alt1.gmail-smtp-in.l.google.com
SMTP_TEST_GMAIL_PORT=25

...

"""


def smtp_server_from_env(name='GMAIL'):

    def _var(param, default=None):
        v = os.environ.get('SMTP_TEST_{}_{}'.format(name, param), default)
        return v

    def _valid_smtp(data):
        return data['host']

    smtp_info = dict(
        from_email=_var("FROM", default=DEFAULT_FROM),
        to_email=_var("TO"),
        host=_var('HOST'),
        port=_var('PORT', default=25),
        user=_var('USER'),
        password=_var('PASSWORD')
    )

    if _valid_smtp(smtp_info):

        if as_bool(_var('WITH_TLS')):
            smtp_info['tls'] = True
            sys_name = '{}_WITH_TLS'.format(name)
            yield sys_name, smtp_info

        if as_bool(_var('WITHOUT_TLS')):
            smtp_info['tls'] = False
            sys_name = '{}_WITHOUT_TLS'.format(name)
            yield sys_name, smtp_info


class SMTPTestParams(object):

    subject_prefix = '[python-emails]'

    def __init__(self, from_email=None, to_email=None, defaults=None, **kw):
        params = {'fail_silently': False, 'debug': 1, 'timeout': 25}
        params.update(defaults or {})
        params.update(kw)
        self.params = params
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
                                        '// %s' % SUBJECT_SUFFIX])

        message._headers['X-Test-Date'] = datetime.datetime.utcnow().isoformat()
        message._headers['X-Python-Version'] = "%s/%s" % (platform.python_version(), platform.platform())
        message._headers['X-Build-Data'] = SUBJECT_SUFFIX

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


def get_servers():
    names = os.environ.get('SMTP_TEST_SETS', None)
    if names:
        for name in names.split(','):
            for sys_name, params in smtp_server_from_env(name):
                yield sys_name, SMTPTestParams(**params)

