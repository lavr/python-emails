# encoding: utf-8

import string

class BaseTemplate:

    def __init__(self, template_text, **kwargs):
        self.template = template_text

    def render(self, **kwargs):
        raise NotImplemented


class StringTemplate:

    """
    string.Template is very basic template engine.
    Do not use it really.
    """

    def __init__(self, template_text, safe_substitute=True, **kwargs):
        self.template = string.Template(template_text)
        self.safe_substitute = safe_substitute

    def render(self, **kwargs):
        render = self.safe_substitute and self.template.safe_substitute or self.template.substitute
        return render(**kwargs)