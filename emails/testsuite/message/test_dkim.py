import pytest
import emails
from emails import Message
from io import StringIO

from emails.exc import DKIMException
import dkim
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from .helpers import common_email_data


@pytest.fixture(scope="session")
def dkim_keys():
    """Fresh 2048-bit RSA keypair for DKIM tests.

    Returns (private_key_pem, public_key_pem) as bytes.
    Generated once per test session — RSA keygen is slow (~100 ms).
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def _check_dkim(message, pub_key):
    def _plain_public_key(s):
        return b"".join([l for l in s.split(b'\n') if not l.startswith(b'---')])
    message = message.as_string()
    o = dkim.DKIM(message=message.encode())
    return o.verify(dnsfunc=lambda name, **kw: b"".join([b"v=DKIM1; p=", _plain_public_key(pub_key)]))


def test_dkim(dkim_keys):
    priv_key, pub_key = dkim_keys

    DKIM_PARAMS = [dict(key=StringIO(priv_key.decode()),
                        selector='_dkim',
                        domain='somewhere1.net'),

                   dict(key=priv_key,
                        selector='_dkim',
                        domain='somewhere2.net'),

                   # legacy key argument name
                   dict(privkey=priv_key,
                        selector='_dkim',
                        domain='somewhere3.net'),
                   ]

    for dkimparams in DKIM_PARAMS:
        message = Message(**common_email_data())
        message.dkim(**dkimparams)
        # check DKIM header exist
        assert message.as_message()['DKIM-Signature']
        assert 'DKIM-Signature: ' in message.as_string()
        assert _check_dkim(message, pub_key)



def test_dkim_error(dkim_keys):
    priv_key, _ = dkim_keys

    m = emails.html(**common_email_data())

    # No key
    with pytest.raises(TypeError):
        m.dkim(selector='_dkim',
               domain='somewhere.net',
               ignore_sign_errors=False)


    # Error in invalid key
    invalid_key = 'X'
    with pytest.raises(DKIMException):
        m.dkim(key=invalid_key,
               selector='_dkim',
               domain='somewhere.net',
               ignore_sign_errors=False)

    # Error on invalid dkim parameters

    m.dkim(key=priv_key,
           selector='_dkim',
           domain='somewhere.net',
           include_headers=['To'])

    with pytest.raises(DKIMException):
        # include_heades must contain 'From'
        m.as_string()

    # Skip error on ignore_sign_errors=True
    m.dkim(key=priv_key,
           selector='_dkim',
           domain='somewhere.net',
           ignore_sign_errors=True,
           include_headers=['To'])

    m.as_string()
    m.as_message()


def test_dkim_as_bytes(dkim_keys):
    priv_key, _ = dkim_keys
    message = Message(**common_email_data())
    message.dkim(key=priv_key, selector='_dkim', domain='somewhere.net')
    result = message.as_bytes()
    assert isinstance(result, bytes)
    assert b'DKIM-Signature: ' in result


def test_dkim_sign_after_error(dkim_keys):
    """After a sign error with ignore_sign_errors, normal signing still works."""
    priv_key, pub_key = dkim_keys

    # First: sign with invalid include_headers (missing From), error ignored
    m1 = Message(**common_email_data())
    m1.dkim(key=priv_key, selector='_dkim', domain='somewhere.net',
            ignore_sign_errors=True, include_headers=['To'])
    m1.as_string()  # should not raise

    # Second: normal sign with same key must still work
    m2 = Message(**common_email_data())
    m2.dkim(key=priv_key, selector='_dkim', domain='somewhere.net')
    assert _check_dkim(m2, pub_key)


def test_dkim_sign_twice(dkim_keys):

    # Test #44:
    # " if you put the open there and send more than one messages it fails
    #   (the first works but the next will not if you dont seek(0) the dkim file first)"
    # Actually not.
    priv_key, pub_key = dkim_keys

    message = Message(**common_email_data())
    message.dkim(key=StringIO(priv_key.decode()), selector='_dkim', domain='somewhere.net')
    for n in range(2):
        message.subject = 'Test %s' % n
        assert _check_dkim(message, pub_key)
