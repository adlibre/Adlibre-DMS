"""
Module: DMS Docs Django Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""
from django.views.generic.simple import direct_to_template

def index(request):
    return direct_to_template(request, 'docs/index.html')


def documentation_index(request):
    return direct_to_template(request, 'docs/documentation_index.html')


def about_documentation(request):
    return direct_to_template(request, 'docs/about_documentation.html')


def api_documentation(request):
    return direct_to_template(request, 'docs/api_documentation.html')


def technical_documentation(request):
    return direct_to_template(request, 'docs/technical_documentation.html')
