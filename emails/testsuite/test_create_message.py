# encoding: utf-8

import emails

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



if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_renderables()


