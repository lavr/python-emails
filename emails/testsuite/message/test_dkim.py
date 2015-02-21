# coding: utf-8
from __future__ import unicode_literals
import os
import emails
from emails.compat import NativeStringIO, to_bytes


TRAVIS_CI = os.environ.get('TRAVIS')
HAS_INTERNET_CONNECTION = not TRAVIS_CI

KEYSIZE = 1024

DEFAULT_PRIVKEY = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDkAjnzycNmm4NXwTnW0T8p89UpLj/shFyh7UFDucxiRGiUVPdi
F5QkoUvt+BGDd2DqrR42daEypP5/EkkvvMiuR1Yr1JM3/jzioshliVKv8luwbVhK
ir16Utppig8BZ8RTeEOY0xIxCfhoQlO0jyEaVPm9jB/UXmUC9zxt8/5FfQIDAQAB
AoGAEmBjj1R5nTF3eoEmSjv/HUB7s5/4ovVgCeT3V6AH6vuceigG8C76T6F4XyuZ
LcFXXFKrlrQQU+acZF1y7JgIjGxY0zqZ85sIR5EQaTUygTp8eB5TK3ztZFqBvmvE
n9F8pX52AihkN+fRlon/DOqvFgkuaQ58sZQtErURwSNgJkECQQDqKEyI6FoSKBjq
tq96fZ4rn7GPvAUJvFKRamrttlGB4cFM4OEn/ovOfWXQPFJ4CqvEvr1SKVA4k3Ja
QE55YILpAkEA+UcYarnI1w1kW+MSvq7CoYbY1FbgZerlQ7XvanjjjtETU9SuPxM+
SahCidwc5JXdJqYZrSGl72hZjGMORF5JdQJBALRBr6FZVTVS/tN5LR8bou6sMdGX
iT1UZy+gf45dYuOceeUH3Oyf7NpZ+E3UkhvtAwwjVbTxLttOzqIhjQetPzkCQQCw
cTZDNMWIEp6au5ulBKYXFw+bHPMwsJce2kRgpLjNegeoKr47Py+zizmtwvNgiQNE
PAWomkyNrNrVl7edhO+RAkEA4aC38DCBs3Y3NVFQvyRn3oRjDuAv04RxiSnd9XBi
TQR25Ou2gNcYS33ddgnIrCLOjxcdrzORNcUitXjy3qsEfQ==
-----END RSA PRIVATE KEY-----"""


def _generate_privkey():

    try:
        # From: http://stackoverflow.com/questions/3504955/using-rsa-in-python
        from Crypto.PublicKey import RSA
        private = RSA.generate(KEYSIZE)
        public = private.publickey()
        privkey = private.exportKey()
    except ImportError:
        privkey = DEFAULT_PRIVKEY

    return to_bytes(privkey)


def test_dkim():

    message = emails.html(html='<p>This is the end, beautiful friend<br>'
                               'This is the end, my only friend',
                          subject='Hello, world!',
                          message_id=False,
                          mail_from=('Jim', 'jim@somewhere.net'),
                          mail_to='Anyone <anyone@here.net>')

    message.attach(data=NativeStringIO('x' * 10), filename='Data.dat')

    message.dkim(privkey=_generate_privkey(), selector='_dkim', domain='somewhere.net',
                 ignore_sign_errors=False)

    # check that DKIM header exist
    assert message.message()['DKIM-Signature']