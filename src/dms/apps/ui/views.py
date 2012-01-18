"""
Module: DMS UI Django Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import json

from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template

from ui.forms import CalendarForm
from api.handlers import FileHandler

def get_urls(id_rule = None, document_name = None):
    c = {   'rules_url': reverse('api_rules', kwargs = {'emitter_format': 'json'}),}
    if id_rule:
        c.update({
            'documents_url': reverse("api_file_list", kwargs = {'id_rule': id_rule}),
            'tags_url': reverse('api_tags', kwargs = {'emitter_format': 'json', 'id_rule': id_rule}),
            })
    if document_name:
        c.update({  'document_url': reverse("api_file") + "?filename=%s" % document_name,
                    'document_info_url': reverse("api_file_info") + "?filename=%s" % document_name
                    })
    return json.dumps(c)

def rule_list(request):
    template_name = "ui/rule_list.html"
    c = {   'communicator_options': get_urls(),}
    return direct_to_template(request, template_name, c)

def document_list(request, id_rule):
    template_name = "ui/document_list.html"
    c = {'communicator_options': get_urls(id_rule = id_rule),
        'rule_id': id_rule,
        'calendar_form': CalendarForm()}
    return direct_to_template(request, template_name, c)

def document(request, document_name):
    template_name = "ui/document.html"
    c = {'communicator_options': get_urls(document_name = document_name),
        'document_name': document_name}
    return direct_to_template(request, template_name, c)

def upload_document(request):
    document_name = FileHandler().create(request)
    if type(document_name) == unicode:
        return document(request, document_name)
    return HttpResponse(str(document_name))
