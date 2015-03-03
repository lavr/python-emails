# coding: utf-8
from __future__ import unicode_literals
import os

import emails
from emails.compat import StringIO
from emails.template import JinjaTemplate

TO_EMAIL = 'jbrown@hotmail.tld'
FROM_EMAIL = 'robot@company.tld'

TRAVIS_CI = os.environ.get('TRAVIS')
HAS_INTERNET_CONNECTION = not TRAVIS_CI

def common_email_data(**kw):
    T = JinjaTemplate
    data = {'charset': 'utf-8',
            'subject': T('[python-emails test] Olá {{name}}'),
            'mail_from': ('LÖVÅS HÅVET', FROM_EMAIL),
            'mail_to': ('Pestävä erillään', TO_EMAIL),
            'html': T('<h1>Olá {{name}}!</h1><p>O Lorem Ipsum é um texto modelo da indústria tipográfica e de impressão.'),
            'text': T('Olá, {{name}}!\nO Lorem Ipsum é um texto modelo da indústria tipográfica e de impressão.'),
            'headers': {'X-Mailer': 'python-emails'},
            'message_id': emails.MessageID(),
            'attachments': [
                {'data': 'Sample text.', 'filename': 'κατάσχεση.txt'},
                {'data': 'R0lGODdhAQABAIAAAAAAAAAAACwAAAAAAQABAAAIBQABAAgIADs='.decode('base64'),  # one-pixel gif
                 'filename': 'pixel.gif'}
            ]}
    if kw:
        data.update(kw)
    return data
