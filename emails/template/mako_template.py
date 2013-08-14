

# encoding: utf-8

from .base import BaseTemplate

try:
    import mako.template as mako_template
except ImportError:
    mako_template = None


class MakoTemplate(BaseTemplate):

    def __init__(self, template_text, **kwargs):

        if mako_template is None:
            raise ImportError("Module 'mako' not found")

        self.template = mako_template.Template(template_text)

    def render(self, **kwargs):
        return self.template.render(**kwargs)

