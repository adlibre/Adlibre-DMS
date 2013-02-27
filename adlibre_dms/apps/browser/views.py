"""
Module: DMS Browser Django Views

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import logging

from djangoplugins import models as plugin_models
from djangoplugins.models import Plugin

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.simple import direct_to_template
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from dms_plugins import models, forms, representator
from dms_plugins.operator import PluginsOperator
from core.document_processor import DocumentProcessor
from browser.forms import UploadForm
from core.http import DocumentResponse

# FIXME: temporary logger
#log = logging.getLogger('browser')
log = logging.getLogger('')

def index(request):
    return direct_to_template(request, 'browser/index.html')

# TODO : These should all have pagination
# TODO : These should use the WS API to browse the repository to reduce code duplication and to have pure separation.


# FIXME: Need to fix the @staff_required decorator to redirect to standard login form
# I don't think we want to necessarily use the django admin login.
def upload(request, template_name='browser/upload.html', extra_context={}):
    """
    Upload file processing.

    Uploaded file will be check against available rules to
    determine storage, validator, and security plugins.
    """

    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            processor = DocumentProcessor()
            upl_file = form.files['file']
            # finding file in system. Updating if found and storing new if not.
            processor.read(upl_file.name, {'user': request.user, 'only_metadata': True})
            if not processor.errors:
                processor.update(upl_file.name, {'user': request.user, 'update_file': upl_file})
            else:
                processor.errors = []
                processor.create(upl_file, {'user': request.user})
            # Handling processor errors in interactions.
            if not processor.errors:
                messages.success(request, 'File has been uploaded.')
                log.info('browser.upload file: %s sucess' % form.files['file'].name)
            else:
                error_string = "; ".join([unicode(x) for x in processor.errors])
                messages.error(request, error_string)
                log.error('browser.upload errror: %s' % error_string)

    extra_context['form'] = form
    return direct_to_template(request,
                              template_name,
                              extra_context=extra_context)

def error_response(errors):
    error = errors[0]
    response = HttpResponse(error.parameter)
    response.status_code = error.code
    return response

def get_file(request, code, suggested_format=None):
    hashcode = request.GET.get('hashcode', None) # Refactor me out
    processor = DocumentProcessor()
    options = {
        'hashcode': hashcode,
        'extension': suggested_format,
        'user': request.user,
    }
    document = processor.read(code, options)
    if processor.errors:
        response = error_response(processor.errors)
    else:
        response = DocumentResponse(document)
    return response

@staff_member_required
def revision_document(request, document):
    document_name = document
    processor = DocumentProcessor()
    document = processor.read(document_name, options={'only_metadata':True, 'user': request.user,})
    extra_context = {}
    metadata = document.get_metadata()
    def get_args(fileinfo):
        args = []
        for arg in ['revision', 'hashcode']:
            if fileinfo.get(arg, None):
                args.append("%s=%s" % (arg, fileinfo[arg]))
        arg_string = ""
        if args:
            arg_string = "?" + "&".join(args)
        return arg_string
    if not processor.errors:
        if metadata:
            revisions = map(lambda x: int(x), metadata.keys())
            revisions.sort()
            fileinfos = []
            for revision in revisions:
                fileinfo = metadata[str(revision)]
                fileinfo['args'] = get_args(fileinfo)
                fileinfos.append(fileinfo)
            extra_context = {
                'fileinfo_db': fileinfos,
                'document_name': document.get_stripped_filename(),
            }
        else:
            fileinfo = {    'revision': None, 
                            'name': document.get_filename(), 
                            'created_date': document.get_creation_time(),
                            'hashcode': document.get_hashcode(),
                        }
            fileinfo['args'] = get_args(fileinfo)
            extra_context = {
                'fileinfo_db': [fileinfo],
                'document_name': document.get_filename(),
            }
    else:
        t = processor.errors
        messages.error(request, "; ".join(map(lambda x: x.parameter, processor.errors)))
    if processor.warnings:
        messages.warning(request, "; ".join(processor.warnings))
    return direct_to_template(request, 'browser/revision.html',
            extra_context=extra_context)

@staff_member_required
def files_index(request):
    mappings = models.DoccodePluginMapping.objects.all()
    extra_context = {'rules': mappings}
    return direct_to_template(request, 'browser/files_index.html',
            extra_context=extra_context)

@staff_member_required
def files_document(request, id_rule):
    mapping = get_object_or_404(models.DoccodePluginMapping, pk = id_rule)
    operator = PluginsOperator()
    file_list = operator.get_file_list(mapping)
    extra_context = {
        'mapping': mapping,
        'document_list': file_list,
    }
    return direct_to_template(request, 'browser/files.html',
            extra_context = extra_context)
#settings

@staff_member_required
def plugins(request, template_name='browser/plugins.html',
            extra_context={}):
    """
    List of available plugins
    """
    operator = PluginsOperator()
    plugins = operator.get_plugin_list()
    extra_context['plugin_list'] = plugins

    return direct_to_template(request, template_name, extra_context=extra_context)

@staff_member_required
def setting(request, template_name='browser/setting.html',
            extra_context={}):
    """
    Setting for adding and editing rule.
    """
    mappings = models.DoccodePluginMapping.objects.all()
    plugins = Plugin.objects.all()
    kwargs = representator.create_form_fields(plugins)
    form = forms.PluginSelectorForm()
    form.setFields(kwargs)
    
    if request.method == 'POST':
        form.setData(request.POST)
        if form.validation_ok():
            representator.save_PluginSelectorForm(request.POST, plugins)
            return HttpResponseRedirect('.')
    extra_context['form'] = form
    extra_context['rule_list'] = mappings
    return direct_to_template(request, template_name, extra_context=extra_context)

@staff_member_required
def edit_setting(request, rule_id, template_name='browser/edit_setting.html',
                   extra_context={}):
    mapping = get_object_or_404(models.DoccodePluginMapping, id=rule_id)
    instance = representator.serialize_model_for_PluginSelectorForm(mapping)
    plugins = Plugin.objects.all()
    kwargs = representator.create_form_fields(plugins)
    form = forms.PluginSelectorForm(initial = instance)
    form.setFields(kwargs)
    
    if request.method == 'POST':
        form.setData(request.POST)
        if form.validation_ok():
            representator.save_PluginSelectorForm(request.POST, plugins, rule_id)
            return HttpResponseRedirect('.')
    extra_context['rule'] = mapping
    extra_context['form'] = form
    return direct_to_template(request, template_name, extra_context=extra_context)


@staff_member_required
def toggle_rule_state(request, rule_id):
    """
    Toggle rule state of being active or disabled
    """
    mapping = get_object_or_404(models.DoccodePluginMapping, id=rule_id)
    mapping.active = not mapping.active
    mapping.save()
    return HttpResponseRedirect(reverse("setting"))

@staff_member_required
def plugin_setting(request, rule_id, plugin_id,
                   template_name='browser/plugin_setting.html',
                   extra_context={}):
    """
    Some plugins have configuration and the configuration can be different for
    each rule.
    """
    mapping = get_object_or_404(models.DoccodePluginMapping, id=rule_id)
    plugin_obj = get_object_or_404(plugin_models.Plugin, id = plugin_id)
    plugin = plugin_obj.get_plugin()
    form = plugin.get_configuration_form(mapping)
    if request.method == 'POST':
        form = plugin.get_configuration_form(mapping, data = request.POST)
        if form.is_valid():
            plugin_option = form.save()
        return HttpResponseRedirect('.')
    extra_context['form'] = form
    extra_context['rule'] = mapping
    extra_context['plugin'] = plugin
    return direct_to_template(request, template_name, extra_context=extra_context)


