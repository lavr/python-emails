# encoding: utf-8
from __future__ import unicode_literals, print_function
import gettext
from emails import Message
from emails.utils import decode_header

def lazy_string(func, string, **variables):
    from speaklater import make_lazy_string
    return make_lazy_string(func, string, **variables)


def test_lazy_translated():
    # prepare translations
    T = gettext.GNUTranslations()
    T._catalog = {'invitation': 'invitaci\xf3n'}
    _ = T.gettext

    msg = Message(html='...', subject=lazy_string(_, 'invitation'))
    assert decode_header(msg.as_message()['subject']) == _('invitation')

    msg = Message(html='...', subject='invitaci\xf3n')
    assert decode_header(msg.as_message()['subject']) == 'invitaci\xf3n'



