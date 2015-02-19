# encoding: utf-8
from __future__ import unicode_literals
import email
import os.path
from emails.loader.fileloader import MsgLoader

def test_msg_fileloader():
    ROOT = os.path.dirname(__file__)
    for i in range(5):
        filename = os.path.join(ROOT, "data/msg/%s.eml" % (i+1))
        msg = email.message_from_string(open(filename).read())
        msgloader = MsgLoader(msg=msg)
        msgloader._parse_msg()
        print filename, msgloader.list_files()
    assert 0