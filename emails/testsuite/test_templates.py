# encoding: utf-8
from __future__ import unicode_literals
from emails.template import MakoTemplate, StringTemplate, JinjaTemplate
from emails.template.base import BaseTemplate

def test_template_cache():
    t = BaseTemplate("A")
    t._template = 'XXX'
    t.set_template_text('B')
    assert t._template is None
    assert t.template_text == 'B'

def test_templates_basics():
    valid_result = "Hello, world!"
    for cls, tmpl in ((StringTemplate, "Hello, ${name}!"),
                      (MakoTemplate, "Hello, ${name}!"),
                      (JinjaTemplate, "Hello, {{name}}!")):
        assert cls(tmpl).render(name='world') == valid_result
