# encode: utfp8
from __future__ import unicode_literals
import emails
from emails.template import JinjaTemplate, StringTemplate, MakoTemplate


def test_templates_commons():
    JINJA_TEMPLATE = "Hello, {{name}}!"
    STRING_TEMPLATE = "Hello, $name!"
    MAKO_TEMPLATE = "Hello, ${name}!"
    RESULT = "Hello, world!"

    values = {'name': 'world'}

    assert JinjaTemplate(JINJA_TEMPLATE).render(**values) == RESULT

    assert StringTemplate(STRING_TEMPLATE).render(**values) == RESULT

    assert MakoTemplate(MAKO_TEMPLATE).render(**values) == RESULT


def test_render_message_with_template():
    TEMPLATE = JinjaTemplate('Hello, {{name}}!')
    V = dict(name='world')
    RESULT = TEMPLATE.render(**V)
    assert RESULT == 'Hello, world!'

    msg = emails.html(subject=TEMPLATE)
    msg.render(**V)
    assert msg.subject == RESULT

    msg = emails.html(html=TEMPLATE)
    msg.render(**V)
    assert msg.html_body == RESULT

    msg = emails.html(text=TEMPLATE)
    msg.render(**V)
    assert msg.text_body == RESULT
