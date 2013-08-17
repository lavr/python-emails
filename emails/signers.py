# encoding: utf-8

# This module use pydkim for DKIM signature

# Special note for python2.4 users:
#  - use dkimpy v0.3 from http://hewgill.com/pydkim/
#  - install hashlib (https://pypi.python.org/pypi/hashlib/20081119) and dnspython
from __future__ import unicode_literals
import logging

from emails.packages import dkim

class DKIMSigner:

    def __init__(self, selector, domain, privkey, ignore_sign_errors=True, **kwargs):

        self.ignore_sign_errors = ignore_sign_errors
        self._sign_params = kwargs

        if privkey and hasattr(privkey, 'read'):
            privkey = privkey.read()

        self._sign_params.update({'privkey':privkey, 'domain': domain, 'selector':selector})


    def sign(self, message):

        dkim_header = None

        try:
            # TODO:
            #  pydkim module parses message and privkey on each signing
            #  this is not optimal for our purposes
            #  we need patch for pydkim or just another signing module
            dkim_header = dkim.sign(message=message, **self._sign_params)
        except:
            if self.ignore_sign_errors:
                logging.exception('Error signing message')
                dkim_header = "X-DKIM-Signature-Failed: yes\r\n"
            else:
                raise

        return dkim_header
