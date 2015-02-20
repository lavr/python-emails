# encoding: utf-8
from __future__ import unicode_literals
import emails
from emails.compat import to_unicode
import emails.loader
from emails.compat import urlparse
import lxml
import lxml.etree

import os.path

def test_load_from_url():
    base_url = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/'
    url = base_url + 'template-widgets.html'
    loader = emails.loader.from_url(url)
    valid_images = [u'images/spacer.gif', u'images/widget-logo4.png', u'images/widget-hero3.png', u'images/gallery.png', u'images/flickr.gif', u'images/twitter.gif', u'images/facebook.gif']
    valid_images = [base_url + name for name in valid_images]
    assert sorted(valid_images) == sorted(loader.transformer.attachment_store.keys())


def test_just_load():
    # Load some sites.
    # Loader just shouldn't throw exception
    URLs = [
        'https://github.com/lavr/python-emails',
        #'http://cnn.com',
        'http://yandex.com',
        #'http://youtube.com',
        #'http://www.smashingmagazine.com/'
    ]

    for url in URLs:
        emails.loader.from_url(url)

