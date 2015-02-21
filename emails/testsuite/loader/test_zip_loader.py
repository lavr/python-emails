# encoding: utf-8
from __future__ import unicode_literals
import emails
import emails.loader
import os.path

ROOT = os.path.dirname(__file__)

def test_load_zip():
    filename = os.path.join(ROOT, "data/html_import/oldornament.zip")
    loader = emails.loader.from_zip(open(filename, 'rb'))
    attachment_store = loader.transformer.attachment_store
    assert len(list(attachment_store.keys())) >= 13
    assert "SET-3-old-ornament" in loader.transformer.to_string()

