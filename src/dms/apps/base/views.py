import os
import pickle

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader

from base.forms import UploadForm, SettingForm, EditSettingForm
from base.models import (Rule, available_validators, available_doccodes,
    available_storages, available_securities)

from base.dms import DmsBase, DmsRule, DmsDocument, DmsException


def handlerError(request, httpcode, message):
    t = loader.get_template(str(httpcode)+'_custom.html')
    context = RequestContext(
        request, {'request_path': request.path,
                  'message': message, }
        )
    response = HttpResponse(t.render(context))
    response.status_code = httpcode
    return response

# FIXME: Need to fix the @staff_required decorator to redirect to standard login form
# I don't think we want to necessarily use the django admin login.
@login_required
def upload(request, template_name='base/upload.html', extra_context={}):
    """
    Upload file processing. Uploaded file will be check against available rules to
    determine storage, validator, and security plugins.
    """

    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            document = os.path.splitext(form.files['file'].name)[0]

            try:
                d = DmsDocument(document)
            except DmsException, (e):
                return handlerError(request, e.code, e.parameter)

            file_content = form.files['file']
            d.set_file(request, file_content, new_revision=True, append_content=False) # TODO: Add Exception check.
            messages.success(request, 'File has been uploaded.')

    extra_context['form'] = form
    return direct_to_template(request,
                              template_name,
                              extra_context=extra_context)


def get_file(request, document, hashcode=None, extension=None):

    revision = request.GET.get("r", None)
    request_extension = extension

    try:
        d = DmsDocument(document, revision)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    try:
        content, filename, mimetype = d.get_file(request, hashcode, request_extension)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)
    except Exception, (e):
        return handlerError(request, 500, e) # Generic Exception. All others should be caught above by DmsException
    else:
        response = HttpResponse(content, mimetype=mimetype)
        response["Content-Length"] = len(content)
        response['Content-Disposition'] = 'filename=%s' % filename
        return response


@staff_member_required
def revision_document(request, document):

    try:
        d = DmsDocument(document)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    extra_context = {
        'fileinfo_db': d.get_meta_data(request),
        'document': document,
    }

    if d.get_hash():
        extra_context['hash'] = d.get_hash

    return direct_to_template(request, 'base/revision.html',
        extra_context=extra_context)


@staff_member_required
def files_index(request):

    try:
        dms = DmsBase()
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    try:
        rules = dms.get_rules()
    except:
        return handlerError(request, 500, "No rules found")
    else:
        extra_context = {
            'rules': rules,
            }
    
        return direct_to_template(request, 'base/files_index.html',
            extra_context=extra_context)


# TODO : Add pagination
# TODO : This should use the WS API to browse the repository
@staff_member_required
def files_document(request, id_rule):

    try:
        dms = DmsRule(id_rule)
    except DmsException, (e):
        return handlerError(request, e.code, e.parameter)

    rule_context = {
        'id': dms.rule.id,
        'name': dms.rule.get_doccode().name,
        }
    extra_context = {
        'document_list': dms.get_file_list(),
        'rule': rule_context,
        }

    return direct_to_template(request, 'base/files.html',
        extra_context=extra_context)


@staff_member_required
def setting(request, template_name='base/setting.html',
            extra_context={}):
    """
    Setting for adding and editing rule.
    """
    rule_list = Rule.objects.all()
    if request.method == 'POST':
        form = SettingForm(request.POST)
        if form.is_valid():
            rule = Rule()
            rule.doccode = pickle.dumps(DocCodeProvider.plugins[form.cleaned_data['doccode']]())
            rule.storage = pickle.dumps(StorageProvider.plugins[form.cleaned_data['storage']]())
            rule.securities = pickle.dumps([SecurityProvider.plugins[item]()
                for item in form.cleaned_data['securities']])
            rule.validators = pickle.dumps([ValidatorProvider.plugins[item]()
                for item in form.cleaned_data['validators']])
            rule.save()
            messages.success(request, 'New rule added.')
    else:
        form = SettingForm()
    extra_context['form'] = form
    extra_context['rule_list'] = rule_list
    return direct_to_template(request, template_name, extra_context=extra_context)


@staff_member_required
def edit_setting(request, rule_id, template_name='base/edit_setting.html',
                   extra_context={}):
    rule = get_object_or_404(Rule, id=rule_id)
    initial = {
        'storage':rule.get_storage().name,
        'validators':[item.name for item in rule.get_validators()],
        'securities':[item.name for item in rule.get_securities()]
    }
    form = EditSettingForm(request.POST or initial)
    if request.method == 'POST':
        if form.is_valid():
            rule.storage = pickle.dumps(StorageProvider.plugins[form.cleaned_data['storage']]())
            rule.securities = pickle.dumps([SecurityProvider.plugins[item]()
                for item in form.cleaned_data['securities']])
            rule.validators = pickle.dumps([ValidatorProvider.plugins[item]()
                for item in form.cleaned_data['validators']])
            rule.save()
            messages.success(request, 'Rule details updated.')
            return HttpResponseRedirect(reverse('setting'))

    extra_context['rule'] = rule
    extra_context['form'] = form
    return direct_to_template(request, template_name, extra_context=extra_context)


@staff_member_required
def toggle_rule_state(request, rule_id):
    """
    Toggle rule state of being active or disabled
    """

    rule = get_object_or_404(Rule, id=rule_id)
    rule.active = not rule.active
    rule.save()
    return HttpResponseRedirect(reverse("setting"))


@staff_member_required
def toggle_securities_plugin(request, rule_id, plugin_index):
    rule = get_object_or_404(Rule, id=rule_id)
    plugins = rule.get_securities()
    plugin = plugins[int(plugin_index)]
    plugin.active = not plugin.active
    plugins[int(plugin_index)] = plugin
    rule.securities = pickle.dumps(plugins)
    rule.save()
    return HttpResponseRedirect(reverse("setting"))


@staff_member_required
def toggle_validators_plugin(request, rule_id, plugin_index):
    rule = get_object_or_404(Rule, id=rule_id)
    plugins = rule.get_validators()
    plugin = plugins[int(plugin_index)]
    plugin.active = not plugin.active
    plugins[int(plugin_index)] = plugin
    rule.validators = pickle.dumps(plugins)
    rule.save()
    return HttpResponseRedirect(reverse("setting"))


@staff_member_required
def plugins(request, template_name='base/plugins.html',
            extra_context={}):
    """
    List of available plugins
    """

    plugins = available_doccodes()
    plugins.update(available_validators())
    plugins.update(available_securities())
    plugins.update(available_storages())
    extra_context['plugin_list'] = plugins

    return direct_to_template(request, template_name, extra_context=extra_context)


@staff_member_required
def plugin_setting(request, rule_id, plugin_type, plugin_index,
                   template_name='base/plugin_setting.html',
                   extra_context={}):
    """
    Some plugins have configuration and the configuration can be different for
    each rule.
    """

    rule = get_object_or_404(Rule, id=rule_id)
    if plugin_type == 'validator':
        plugins = rule.get_validators()
    else:
        plugins = rule.get_securities()
    plugin = plugins[int(plugin_index)]
    formclass = plugin.get_form()
    form = formclass(plugin, request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            plugins[int(plugin_index)] = plugin
            if plugin_type == 'validator':
                rule.validators = pickle.dumps(plugins)
            else:
                rule.securities = pickle.dumps(plugins)
            rule.save()
    extra_context['plugin'] = plugin
    extra_context['rule'] = rule
    extra_context['form'] = form

    return direct_to_template(request, template_name, extra_context=extra_context)


@staff_member_required
def plugin_action(request, rule_id, plugin_type, plugin_index, action,
                   extra_context={}):
    """

    """

    rule = get_object_or_404(Rule, id=rule_id)
    if plugin_type == 'validator':
        plugins = rule.get_validators()
    else:
        plugins = rule.get_securities()
    plugin = plugins[int(plugin_index)]
    view = plugin.action(action)
    return view(request, rule, plugin, rule_id, plugin_type, plugin_index)


def index(request):
    return direct_to_template(request, 'base/index.html')


def documentation_index(request):
    return direct_to_template(request, 'base/documentation_index.html')


def about_documentation(request):
    return direct_to_template(request, 'base/about_documentation.html')


def api_documentation(request):
    return direct_to_template(request, 'base/api_documentation.html')


def technical_documentation(request):
    return direct_to_template(request, 'base/technical_documentation.html')
