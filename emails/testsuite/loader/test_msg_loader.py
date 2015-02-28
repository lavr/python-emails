# encoding: utf-8
from __future__ import unicode_literals, print_function
import os.path
import pytest
import emails.loader
from emails.loader.local_store import (MsgLoader, FileSystemLoader, FileNotFound, ZipLoader,
                                       split_template_path, BaseLoader)
from emails.compat import text_type
from emails.loader.helpers import guess_charset

ROOT = os.path.dirname(__file__)

def _get_rfc_message():
    m = emails.loader.from_zip(open(os.path.join(ROOT, "data/html_import/oldornament.zip"), 'rb'))
    n = len(m.attachments)
    for i, a in enumerate(m.attachments):
        a.content_disposition = 'inline' if i < n/2 else 'attachment'
    m.transformer.synchronize_inline_images()
    m.transformer.save()
    #open('oldornament.eml', 'wb').write(m.as_string())
    return m.as_string()

@pytest.mark.xfail
def test_rfc822_loader(**kw):
    message = emails.loader.from_rfc822(_get_rfc_message(), **kw)
    #print(message.html)

    assert len(message.transformer.local_loader._files) == 14
    #message.attachments.by_filename('arrow.png').data

    assert len(message.attachments.keys()) == 13

    valid_filenames = ['arrow.png', 'banner-bottom.png', 'banner-middle.gif', 'banner-top.gif', 'bg-all.jpg',
                       'bg-content.jpg', 'bg-main.jpg', 'divider.jpg', 'flourish.png', 'img01.jpg', 'img02.jpg',
                       'img03.jpg', 'spacer.gif']
    assert sorted([a.filename for a in message.attachments]) == sorted(valid_filenames)
    print(type(message.attachments))
    assert len(message.attachments.by_filename('arrow.png').data) == 484

    # Simple html content check
    html = normalize_html(message.html)
    assert 'Lorem Ipsum Dolor Sit Amet' in html
    htmls.append(html)

    # Simple string check
    rfc_string = message.as_string()
    rfc_strings.append(rfc_string)