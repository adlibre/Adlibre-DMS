"""
Module: DMS UI Django Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import os
import json

from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from ui.forms import CalendarForm
from api.handlers import FileHandler

def get_urls(id_rule=None, document_name=None):
    c = {   'rules_url': reverse('api_rules', kwargs={'emitter_format': 'json'}),}
    if id_rule:
        c.update({
            'documents_url': reverse("api_file_list", kwargs={'id_rule': id_rule}),
            'tags_url': reverse('api_tags', kwargs={'emitter_format': 'json', 'id_rule': id_rule}),
            })
    if document_name:
        code, suggested_format = os.path.splitext(document_name)
        suggested_format = suggested_format[1:] # Remove . from file ext
        if suggested_format == '':
            c.update({  'document_url': reverse('api_file', kwargs={'code': code,}),
                        'document_info_url': reverse('api_file', kwargs={'code': code,}),
                        })
        else:
            c.update({  'document_url': reverse('api_file', kwargs={'code': code,'suggested_format': suggested_format,}),
                        'document_info_url': reverse('api_file', kwargs={'code': code,'suggested_format': suggested_format,}),
                        })
    return json.dumps(c)

@login_required
def rule_list(request):
    template_name = "ui/rule_list.html"
    c = {   'communicator_options': get_urls(),}
    return direct_to_template(request, template_name, c)

@login_required
def document_list(request, id_rule):
    template_name = "ui/document_list.html"
    c = {'communicator_options': get_urls(id_rule=id_rule),
        'rule_id': id_rule,
        'calendar_form': CalendarForm()}
    return direct_to_template(request, template_name, c)

@login_required
def document(request, document_name):
    template_name = "ui/document.html"
    c = {'communicator_options': get_urls(document_name=document_name),
        'document_name': document_name}
    return direct_to_template(request, template_name, c)

@login_required
def upload_document(request):
    # FIXME: Refactor out this direct calling of api.
    document_name = FileHandler().create(request, None, None)
    if type(document_name) == unicode:
        return document(request, document_name)
    return HttpResponse(str(document_name))
