# encoding: utf-8
import logging
from secure_smtpd import SMTPServer, LOG_NAME
import sys

class SSLSMTPServer(SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, message_data):
        print(message_data)
        with open('secure-smtpd.log', 'a') as f:
            f.write(message_data)
            f.write('\n\n')

class MyCredentialValidator(object):
    def validate(self, username, password):
        if username == 'A' and password == 'B':
            return True
        return False

logger = logging.getLogger(LOG_NAME)
logger.setLevel(logging.INFO)

params = {}
port = 25125

if 'auth' in sys.argv:
    params.update({'require_authentication': True, 'credential_validator': MyCredentialValidator()})
    port = 25127

if 'ssl' in sys.argv:
    params.update({'ssl': True, 'certfile': 'example.crt', 'keyfile': 'example.key'})
    port = 25126

if 'timeout':
    params.update({'maximum_execution_time': 10.0})

server = SSLSMTPServer(('127.0.0.1', port), None, **params)
server.run()