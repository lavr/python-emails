# encoding: utf-8

import emails

try:
    from local_settings import SMTP_SERVER, SMTP_PORT, SMTP_SSL, SMTP_USER, SMTP_PASSWORD
    SMTP_DATA = {'host': SMTP_SERVER, 'port': SMTP_PORT,
                 'ssl': SMTP_SSL, 'user': SMTP_USER, 'password': SMTP_PASSWORD,
                 'debug': 0}
except ImportError:
    SMTP_DATA = None


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


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    #test_send_inline_images()
    #test_send2()
    test_send1()

