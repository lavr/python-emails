# coding: utf-8
from __future__ import unicode_literals

import logging
import os

from emails.loader import cssinliner
import emails
from emails.compat import StringIO
from emails.template import JinjaTemplate
from emails.compat import NativeStringIO, to_bytes

TRAVIS_CI = os.environ.get('TRAVIS')
HAS_INTERNET_CONNECTION = not TRAVIS_CI

def common_email_data(**kwargs):
    data = {'charset': 'utf-8',
            'subject': 'Что-то по-русски',
            'mail_from': ('Максим Иванов', 'ivanov@ya.ru'),
            'mail_to': ('Полина Сергеева', 'polina@mail.ru'),
            'html': '<h1>Привет!</h1><p>В первых строках...',
            'text': 'Привет!\nВ первых строках...',
            'headers': {'X-Mailer': 'python-emails'},
            'attachments': [{'data': 'aaa', 'filename': 'Event.ics'},
                            {'data': StringIO('bbb'), 'filename': 'map.png'}],
            'message_id': emails.MessageID()}

    if kwargs:
        data.update(kwargs)

    return data


def _email_data(**kwargs):
    T = JinjaTemplate
    data = {'charset': 'utf-8',
            'subject': T('Hello, {{name}}'),
            'mail_from': ('Максим Иванов', 'sergei-nko@mail.ru'),
            'mail_to': ('Полина Сергеева', 'sergei-nko@mail.ru'),
            'html': T('<h1>Привет, {{name}}!</h1><p>В первых строках...'),
            'text': T('Привет, {{name}}!\nВ первых строках...'),
            'headers': {'X-Mailer': 'python-emails'},
            'attachments': [
                {'data': 'aaa', 'filename': 'Event.ics'},
                {'data': 'bbb', 'filename': 'map.png'}
            ]}
    if kwargs:
        data.update(kwargs)
    return data