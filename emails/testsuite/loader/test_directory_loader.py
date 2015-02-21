# encoding: utf-8
from __future__ import unicode_literals
import emails
import emails.loader
import os.path


def test_file_loader():
    ROOT = os.path.dirname(__file__)

    index_file = "data/html_import/colordirect/html/left_sidebar.html"
    loader = emails.loader.from_file(os.path.join(ROOT, index_file))

    ALL_FILES = "bg_divider_top.png,bullet.png,img.png,img_deco_bottom.png,img_email.png," \
                "bg_email.png,ico_lupa.png,img_deco.png".split(',')
    ALL_FILES = set(["images/" + n for n in ALL_FILES])

    files = set(loader.transformer.attachment_store.keys())

    not_attached = ALL_FILES - files
    assert len(not_attached) == 0, "Not attached files found: %s" % not_attached
    assert len(files - ALL_FILES) == 0, "Files set mismatch: %s" % (files - ALL_FILES)



def test_file_loader_2():
    ROOT = os.path.dirname(__file__)

    for fn in ("data/html_import/colordirect/html/full_width.html",
               "data/html_import/oldornament/html/full_width.html"):
        filename = os.path.join(ROOT, fn)
        print(fn)
        loader = emails.loader.from_file(filename)


