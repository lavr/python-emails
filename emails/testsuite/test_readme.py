# encoding: utf-8

import emails, emails.loader

def test_loader_example():

    base_url = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/'
    URL = base_url + 'template-widgets.html'

    message = emails.Message.from_loader(loader=emails.loader.from_url(URL),
                                         mail_from=('ABC', 'robot@mycompany.com'),
                                         subject="Newsletter")

    print(message.as_string())
