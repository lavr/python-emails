# encoding: utf-8
from __future__ import unicode_literals
from .base import BaseTemplate


class JinjaTemplate(BaseTemplate):

    DEFAULT_JINJA_ENVIRONMENT = {}

    def compile_template(self):
        if 'jinja2' not in globals():
            globals()['jinja2'] = __import__('jinja2')
        self.environment = self.kwargs.get('environment', None) or jinja2.Environment(**self.DEFAULT_JINJA_ENVIRONMENT)
        return self.environment.from_string(self.template_text)

    def render(self, **kwargs):
        return self.template.render(**kwargs)

