import json

from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template

def get_communicator_options(request, options = {}):
    options.update()
    return c

def rule_list(request):
    template_name = "ui/rule_list.html"
    c = {'communicator_options': json.dumps({'rules_url': reverse('api_rules', kwargs = {'emitter_format': 'json'})})}
    return direct_to_template(request, template_name, c)

def document_list(request, id_rule):
    template_name = "ui/document_list.html"
    c = {'communicator_options': json.dumps({'documents_url': reverse("api_file_list", kwargs = {'id_rule': id_rule})})}
    return direct_to_template(request, template_name, c)

def document(request, document_name):
    template_name = "ui/document.html"
    c = {'communicator_options': json.dumps({'document_url': reverse("api_file") + "?filename=%s.txt" % document_name})}
    return direct_to_template(request, template_name, c)