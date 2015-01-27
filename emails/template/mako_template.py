# encoding: utf-8
from __future__ import unicode_literals
from .base import BaseTemplate


class MakoTemplate(BaseTemplate):

    def __init__(self, template_text, **kwargs):
        if 'mako_template' not in globals():
            globals()['mako_template'] = __import__('mako.template')
        self.template = mako_template.template.Template(template_text)

    def render(self, **kwargs):
        return self.template.render(**kwargs)


def test_mako_template_1():
    t = MakoTemplate("Hello, ${name}!")
    assert t.render(name='world') == "Hello, world!"