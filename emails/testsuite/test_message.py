# coding: utf-8

import unittest

from emails.loader import cssinliner
from lxml import etree

import emails

from cStringIO import StringIO


try:
    from local_settings import SMTP_SERVER, SMTP_PORT, SMTP_SSL, SMTP_USER, SMTP_PASSWORD
    SMTP_DATA = {'host': SMTP_SERVER, 'port': SMTP_PORT,
                 'ssl': SMTP_SSL, 'user': SMTP_USER, 'password': SMTP_PASSWORD,
                 'debug': 0}
except ImportError:
    SMTP_DATA = None


def test_renderables():

    TEMPLATE = emails.template.JinjaTemplate('Hello, {{name}}!')
    V = dict(name='world')
    RESULT = TEMPLATE.render(**V)
    assert RESULT=='Hello, world!'

    msg = emails.html(subject=TEMPLATE)
    msg.render(**V)
    assert msg.subject == RESULT

    msg = emails.html(html=TEMPLATE)
    msg.render(**V)
    assert msg.html_body == RESULT

    msg = emails.html(text=TEMPLATE)
    msg.render(**V)
    assert msg.text_body == RESULT




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
    m = emails.Message(**kwargs)
    print(m.as_string())



def _email_data(**kwargs):
    T = emails.template.JinjaTemplate
    data = {}
    data['charset'] = 'utf-8'
    data['subject'] = T(u'Hello, {{name}}')
    data['mail_from'] = ('Максим Иванов', 'sergei-nko@mail.ru')
    data['mail_to'] = ('Полина Сергеева', 'sergei-nko@mail.ru')
    data['html'] = T(u'<h1>Привет, {{name}}!</h1><p>В первых строках...')
    data['text'] = T(u'Привет, {{name}}!\nВ первых строках...')
    data['headers'] = {'X-Mailer': 'python-emails'}
    data['attachments'] = [
        {'data': 'aaa', 'filename': 'Event.ics'},
        {'data': 'bbb', 'filename': 'map.png'}
    ]
    if kwargs:
        data.update(kwargs)
    return data


def test_send1():
    URL = 'http://icdn.lenta.ru/images/2013/08/07/14/20130807143836932/top7_597745dde10ef36605a1239b0771ff62.jpg'
    data = _email_data()
    data['attachments'] = [emails.store.LazyHTTPFile(uri=URL), ]
    m = emails.html(**data)
    m.render(name=u'Полина')
    print "m.subject=", m.subject
    assert m.subject==u'Hello, Полина'
    print m.as_string()

    try:
        m.send(smtp=SMTP_DATA)
    except IOError as e:
        print "Error sending emails via %s (%s)" % (SMTP_DATA, e)


def test_send2():
    data = _email_data()
    loader = emails.loader.HTTPLoader(filestore=emails.store.MemoryFileStore())
    #loader = HTTPLoader(  )
    URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html'
    loader.load_url(URL, css_inline=True, make_links_absolute=True, update_stylesheet=True)
    data['html'] = loader.html
    data['attachments'] = loader.attachments_dict
    loader.save_to_file('test_send2.html')
    m = emails.html(**data)
    m.render(name=u'Полина')
    try:
        m.send( smtp=SMTP_DATA )
        m.send( to='s.lavrinenko@gmail.com', smtp=SMTP_DATA )
    except IOError as e:
        print "Error sending emails via %s (%s)" % (SMTP_DATA, e)

def test_send_inline_images():
    data = _email_data()
    loader = emails.loader.HTTPLoader(filestore=emails.store.MemoryFileStore())
    URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html'
    loader.load_url(URL, css_inline=True, make_links_absolute=True, update_stylesheet=True)
    for img in loader.iter_image_links():
        link = img.link
        file = loader.filestore.by_uri(link, img.link_history)
        img.link = "cid:%s" % file.filename
    for file in loader.filestore:
        file.content_disposition = 'inline'
    data['html'] = loader.html
    data['attachments'] = loader.attachments_dict
    #loader.save_to_file('test_send_inline_images.html')
    #print loader.html
    m = emails.html(**data)
    m.render(name=u'Полина')


    try:
        m.send( smtp=SMTP_DATA )
        m.send( to='s.lavrinenko@gmail.com', smtp=SMTP_DATA )
        m.send( to='sergey.lavrinenko@yahoo.com', smtp=SMTP_DATA )
    except IOError as e:
        print "Error sending emails via %s (%s)" % (SMTP_DATA, e)


def _generate_privkey():

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

    try:
        # From: http://stackoverflow.com/questions/3504955/using-rsa-in-python
        from Crypto.PublicKey import RSA
        private = RSA.generate(KEYSIZE)
        public  = private.publickey()
        privkey = private.exportKey()
    except ImportError:
        privkey = DEFAULT_PRIVKEY

    return privkey


def test_dkim():
    data = {}
    message = emails.html(html='<p>This is the end, beautiful friend<br>'\
                               'This is the end, my only friend',
                          subject='Hello, world!',
                          mail_from=('Jim', 'jim@somewhere.net'),
                          mail_to=('Anyone <anyone@here.net>'))

    message.attach( data=StringIO('x'*1024), filename='Data.dat' )

    message.dkim( privkey=_generate_privkey(), selector='_dkim', domain='somewhere.net'   )

    return message.as_string()



if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_dkim()
    test_renderables()
    test_common_mail_build()
    test_send_inline_images()
    test_send2()
    test_send1()
