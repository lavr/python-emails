# coding: utf-8
from __future__ import unicode_literals
import os

import emails
from emails.template import JinjaTemplate

TO_EMAIL = os.environ.get('TEST_TO_EMAIL') or 'python.emails.test.2@yandex.ru'
FROM_EMAIL = os.environ.get('TEST_FROM_EMAIL') or 'python-emails@lavr.me'
ROOT = os.path.dirname(__file__)

def common_email_data(**kw):
    T = JinjaTemplate
    data = {'charset': 'utf-8',
            'subject': T('Olá {{name}}'),
            'mail_from': ('LÖVÅS HÅVET', FROM_EMAIL),
            'mail_to': ('Pestävä erillään', TO_EMAIL),
            'html': T('<h1>Olá {{name}}!</h1><p>O Lorem Ipsum é um texto modelo da indústria tipográfica e de impressão.'),
            'text': T('Olá, {{name}}!\nO Lorem Ipsum é um texto modelo da indústria tipográfica e de impressão.'),
            'headers': {'X-Mailer': 'python-emails'},
            'message_id': emails.MessageID(),
            'attachments': [
                {'data': 'Sample text', 'filename': 'κατάσχεση.txt'},
                {'data': open(os.path.join(ROOT, 'data/pushkin.jpg'), 'rb'), 'filename': 'Пушкин А.С.jpg'}
            ]}
    if kw:
        data.update(kw)
    return data
