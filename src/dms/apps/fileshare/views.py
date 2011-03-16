import mimetypes
import os
import pickle

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext_lazy as _
from django.views.generic.simple import direct_to_template
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


from converter import FileConverter


from fileshare.forms import UploadForm, SettingForm, EditSettingForm
from fileshare.models import (Rule, available_validators, available_doccodes,
    available_storages, available_securities)
from fileshare.utils import ValidatorProvider, StorageProvider, SecurityProvider, DocCodeProvider


@login_required
def upload(request, template_name='fileshare/upload.html', extra_context={}):
    """
    Upload file processing. Uploaded file will be check against available rules to
    determine storage, validator, and security plugins.
    """

    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            document = os.path.splitext(form.files['file'].name)[0]
            rule = Rule.objects.match(document)
            if rule:
                # check against all validator
                for validator in rule.get_validators():
                    if validator.is_storing_action and validator.active:
                        try:
                            validator.perform(request, document)
                        except Exception, e:
                            return HttpResponse(e)

                # check against all securities
                for security in rule.get_securities():
                    if security.is_storing_action and security.active:
                        try:
                            security.perform(request, document)
                        except Exception, e:
                            return HttpResponse(e)


                storage = rule.get_storage()
                storage.store(form.files['file'])
                messages.success(request, 'File has been uploaded.')
            else:
                messages.error(request, "No rule found for your uploaded file")
    extra_context['form'] = form
    return direct_to_template(request,
                              template_name,
                              extra_context=extra_context)


def get_file(request, hashcode, document, extension=None):
    rule = Rule.objects.match(document)
    if not rule:
        raise Http404

    hashplugin = rule.get_security('Hash')
    if hashplugin and not hashplugin.active:
        raise Http404
    # TODO: Make salt / secret key a plugin option
    if hashplugin.perform(document, settings.SECRET_KEY) != hashcode:
        return HttpResponse('Invalid hashcode')

    # check against all validator
    for validator in rule.get_validators():
        if validator.is_retrieval_action and validator.active:
            try:
                validator.perform(request, document)
            except Exception, e:
                return HttpResponse(e)

    # check against all securities
    for security in rule.get_securities():
        if security.is_retrieval_action and security.active:
            try:
                security.perform(request, document)
            except Exception, e:
                return HttpResponse(e)

    revision = request.GET.get("r", None)
    storage = rule.get_storage()
    filepath = storage.get(document, revision)
    if not filepath:
        return HttpResponse("No file match")
    new_file = FileConverter(filepath, extension)
    mimetype, content = new_file.convert()
    if extension:
        filename = "%s.%s" % (document, extension)
    else:
        filename = os.path.basename(filepath)
        rev_document, extension = os.path.splitext(filename)
        filename = "%s%s" % (document, extension)
    response = HttpResponse(content, mimetype=mimetype)
    response["Content-Length"] = len(content)
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response



def get_file_no_hash(request, document, extension = None):
    rule = Rule.objects.match(document)
    if not rule:
        raise Http404

    hashplugin = rule.get_security('Hash')
    if hashplugin and hashplugin.active:
        raise Http404


    # check against all validator
    for validator in rule.get_validators():
        if validator.is_retrieval_action and validator.active:
            try:
                validator.perform(request, document)
            except Exception, e:
                return HttpResponse(e)

    # check against all securities
    for security in rule.get_securities():
        if security.is_retrieval_action and security.active:
            try:
                security.perform(request, document)
            except Exception, e:
                return HttpResponse(e)

    revision = request.GET.get("r", None)
    storage = rule.get_storage()
    filepath = storage.get(document, revision)
    if not filepath:
        return HttpResponse("No file match")
    new_file = FileConverter(filepath, extension)
    try:
        mimetype, content = new_file.convert()
    except TypeError:
        return HttpResponse("No file converter")

    if extension:
        filename = "%s.%s" % (document, extension)
    else:
        filename = os.path.basename(filepath)
        rev_document, extension = os.path.splitext(filename)
        filename = "%s%s" % (document, extension)

    response = HttpResponse(content, mimetype=mimetype)
    response["Content-Length"] = len(content)
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


def revision_document(request, document):
    rule = Rule.objects.match(document)
    if not rule:
        raise Http404

    # check against all validator
    for validator in rule.get_validators():
        if validator.is_retrieval_action and validator.active:
            try:
                validator.perform(request, document)
            except Exception, e:
                return HttpResponse(e)

    # check against all securities
    for security in rule.get_securities():
        if security.is_retrieval_action and security.active:
            try:
                security.perform(request, document)
            except Exception, e:
                return HttpResponse(e)


    storage = rule.get_storage()
    fileinfo_db = storage.revision(document)
    extra_context = {
        'fileinfo_db':fileinfo_db,
        'document':document,

    }
    hashplugin = rule.get_security('Hash')
    if hashplugin and hashplugin.active:
        extra_context['hash'] = hashplugin.perform(document)

    return direct_to_template(request, 'fileshare/revision.html',
        extra_context=extra_context)


# TODO : Add pagination
# TODO : This should use the WS API to browse the repository
# TODO : Add security
def files_document(request, id_rule):
    rule = Rule.objects.get(id=id_rule)
    if not rule:
        raise Http404
    document_list = rule.get_storage().get_list(id_rule)
    rule_context = {
        'id': rule.id,
        'name': rule.get_doccode().name,
        }
    extra_context = {
        'document_list':document_list,
        'rule':rule_context,
        }
    return direct_to_template(request, 'fileshare/documents.html',
        extra_context=extra_context)


@staff_member_required
def setting(request, template_name='fileshare/setting.html',
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
def edit_setting(request, rule_id, template_name='fileshare/edit_setting.html',
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


def plugins(request, template_name='fileshare/plugins.html',
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



def plugin_setting(request, rule_id, plugin_type, plugin_index,
                   template_name='fileshare/plugin_setting.html',
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
    return direct_to_template(request, 'fileshare/index.html')


def documentation_index(request):
    return direct_to_template(request, 'fileshare/documentation_index.html')


def api_documentation(request):
    return direct_to_template(request, 'fileshare/api_documentation.html')


def technical_documentation(request):
    return direct_to_template(request, 'fileshare/technical_documentation.html')
