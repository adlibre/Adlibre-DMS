"""
Module: DMS UI Django Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import os
import json

from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required

from core.document_processor import DocumentProcessor

from ui.forms import CalendarForm


def get_urls(id_rule=None, document_name=None):
    c = {'rules_url': reverse('api_rules'), }
    if id_rule:
        c.update({
            'documents_url': reverse("api_file_list", kwargs={'id_rule': id_rule}),
            'tags_url': reverse('api_tags', kwargs={'id_rule': id_rule}),
        })
    if document_name:
        code, suggested_format = os.path.splitext(document_name)
        suggested_format = suggested_format[1:]  # Remove . from file ext
        if suggested_format == '':
            c.update({
                'document_url': reverse('api_file', kwargs={'code': code, }),
                'document_info_url': reverse('api_file', kwargs={'code': code, }),
            })
        else:
            c.update({
                'document_url': reverse('api_file', kwargs={'code': code, 'suggested_format': suggested_format, }),
                'document_info_url': reverse('api_file', kwargs={'code': code, 'suggested_format': suggested_format, }),
            })
    return json.dumps(c)


@login_required
def rule_list(request):
    template_name = "ui/rule_list.html"

    return render(
        request,
        template_name,
        {
            'communicator_options': get_urls(),
        }
    )


@login_required
def document_list(request, id_rule):
    template_name = "ui/document_list.html"

    return render(
        request,
        template_name,
        {
            'communicator_options': get_urls(id_rule=id_rule),
            'rule_id': id_rule,
            'calendar_form': CalendarForm()
        }
    )


@login_required
def document(request, document_name):
    template_name = "ui/document.html"
    return render(
        request,
        template_name,
        {
            'communicator_options': get_urls(document_name=document_name),
            'document_name': document_name
        }
    )


@login_required
def upload_document(request):
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
    else:
        return HttpResponseBadRequest('File should be present for upload.')
    processor = DocumentProcessor()
    options = {
        'user': request.user,
    }
    d = processor.create(uploaded_file, options)
    if len(processor.errors) > 0:
        return HttpResponseBadRequest('%s' % processor.errors)
    return document(request, d.file_name)
