# encoding: utf-8
from __future__ import unicode_literals
from .base import BaseTemplate


class JinjaTemplate(BaseTemplate):

    DEFAULT_JINJA_ENVIRONMENT = {}

    def __init__(self, template_text, **kwargs):
        if 'jinja2' not in globals():
            globals()['jinja2'] = __import__('jinja2')
        self.environment = kwargs.get('environment', None) or jinja2.Environment(**self.DEFAULT_JINJA_ENVIRONMENT)
        self.template = self.environment.from_string(template_text)

    def render(self, **kwargs):
        return self.template.render(**kwargs)


def test_jinja_template_1():
    t = JinjaTemplate("Hello, {{name}}!")
    assert t.render(name='world') == "Hello, world!"
