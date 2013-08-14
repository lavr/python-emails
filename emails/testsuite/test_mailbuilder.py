# coding: utf-8

import unittest

from emails.loader import cssinliner
from lxml import etree

from emails import Message

from cStringIO import StringIO


def common_email_data(**kwargs):
    data = {}
    data['charset'] = 'utf-8'
    data['subject'] = u'Что-то по-русски'
    data['mail_from'] = ('Максим Иванов', 'ivanov@ya.ru')
    data['mail_to'] = ('Полина Сергеева', 'polina@mail.ru')
    data['html'] = u'<h1>Привет!</h1><p>В первых строках...'
    data['text'] = u'Привет!\nВ первых строках...'
    data['headers'] = {'X-Mailer': 'python-emails'}
    data['attachments'] = [{'data': 'aaa', 'filename': 'Event.ics'},
                           {'data': StringIO('bbb'), 'filename': 'map.png'}]

    if kwargs:
        data.update(kwargs)

    return data


def test_common_mail_build():
    kwargs = common_email_data()
    m = Message(**kwargs)
    print(m.as_string())
