# encoding: utf-8
from __future__ import unicode_literals
import email
import os.path
from emails.loader.fileloader import MsgLoader
import glob

def test_msg_fileloader():
    ROOT = os.path.dirname(__file__)
    for filename in glob.glob(os.path.join(ROOT, "data/msg/*.eml")):
        msg = email.message_from_string(open(filename).read())
        msgloader = MsgLoader(msg=msg)
        msgloader._parse_msg()
        print filename, msgloader.list_files()
    assert 0