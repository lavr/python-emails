from emails.template import JinjaTemplate, StringTemplate, MakoTemplate

def test_jinja_template_1():


    JINJA_TEMPLATE  = "Hello, {{name}}!"
    STRING_TEMPLATE = "Hello, $name!"
    MAKO_TEMPLATE = "Hello, ${name}!"
    RESULT = "Hello, world!"

    values = { 'name': 'world' }

    assert JinjaTemplate(JINJA_TEMPLATE).render(**values) == RESULT

    assert StringTemplate(STRING_TEMPLATE).render(**values) == RESULT

    assert MakoTemplate(MAKO_TEMPLATE).render(**values) == RESULT

