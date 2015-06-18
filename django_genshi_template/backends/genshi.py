from __future__ import absolute_import

import sys

from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends.base import BaseEngine
from django.template.backends.utils import csrf_input_lazy, csrf_token_lazy
from django.utils import six

from genshi.template import TemplateLoader
from genshi.template.base import TemplateSyntaxError \
    as GenshiTemplateSyntaxError, Context as GenshiContext
from genshi.template.loader import TemplateNotFound
from genshi.template.markup import MarkupTemplate


class Genshi(BaseEngine):

    app_dirname = 'genshi'

    def __init__(self, params):
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        self.app_dirname = options.get('app_dirname', self.app_dirname)
        super(Genshi, self).__init__(params)
        auto_reload = options.get('auto_reload', False)
        self.loader = TemplateLoader(self.template_dirs,
                                     auto_reload=auto_reload)
        self.serialization = options.get('serialization', 'html')
        self.doctype = options.get('doctype', 'html')

    def from_string(self, template_code):
        return Template(MarkupTemplate(template_code),
                        self.serialization,
                        self.doctype)

    def get_template(self, template_name):
        try:
            return Template(self.loader.load(template_name),
                            self.serialization,
                            self.doctype)
        except TemplateNotFound as exc:
            six.reraise(TemplateDoesNotExist, TemplateDoesNotExist(exc.args),
                        sys.exc_info()[2])
        except GenshiTemplateSyntaxError as exc:
            six.reraise(TemplateSyntaxError, TemplateSyntaxError(exc.args),
                        sys.exc_info()[2])


class Template(object):

    def __init__(self, template, serialization, doctype):
        self.template = template
        self.serialization = serialization
        self.doctype = doctype

    def render(self, context=None, request=None):
        genshi_context = GenshiContext()
        if request is not None:
            genshi_context['request'] = request
            genshi_context['csrf_input'] = csrf_input_lazy(request)
            genshi_context['csrf_token'] = csrf_token_lazy(request)
        if context is not None:
            genshi_context.push(context)
        stream = self.template.generate(genshi_context)
        # this might raise a genshi.template.eval.UndefinedError (derived from
        # genshi.template.base.TemplateRuntimeError)
        return stream.render(self.serialization, doctype=self.doctype)
