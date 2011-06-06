"""
Module: DMS Base Django Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import os
import pickle

from plugins import models as plugin_models

from django.conf import settings as system_settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.views.generic.simple import direct_to_template

from base.forms import SettingForm, EditSettingForm
from base.models import (Rule, available_validators, available_doccodes,
    available_storages, available_securities)

from base.dms import DmsBase, DmsRule, DmsDocument, DmsException
from base.utils import ValidatorProvider, StorageProvider, SecurityProvider, \
    DocCodeProvider
from dms_plugins import models
from dms_plugins import forms


def handlerError(request, httpcode, message):
    t = loader.get_template(str(httpcode)+'_custom.html')
    context = RequestContext(
        request, {'request_path': request.path,
                  'message': message, }
        )
    response = HttpResponse(t.render(context))
    response.status_code = httpcode
    return response


@staff_member_required
def setting(request, template_name='base/setting.html',
            extra_context={}):
    """
    Setting for adding and editing rule.
    """
    if system_settings.NEW_SYSTEM:
        mappings = models.DoccodePluginMapping.objects.all()
        if request.method == 'POST':
            form = forms.MappingForm(request.POST)
            if form.is_valid():
                mapping = form.save()
                return HttpResponseRedirect('.')
        else:
            form = forms.MappingForm
        extra_context['form'] = form
        extra_context['rule_list'] = mappings
        return direct_to_template(request, "base/new_setting.html", extra_context=extra_context)

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
    if system_settings.NEW_SYSTEM:
        mapping = get_object_or_404(models.DoccodePluginMapping, id=rule_id)
        form = forms.MappingForm(instance = mapping)
        if request.method == 'POST':
            form = forms.MappingForm(instance = mapping, data = request.POST)
            if form.is_valid():
                mapping = form.save()
        extra_context['rule'] = mapping
        extra_context['form'] = form
        return direct_to_template(request, 'base/new_edit_setting.html', extra_context=extra_context)
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
    if system_settings.NEW_SYSTEM:
        mapping = get_object_or_404(models.DoccodePluginMapping, id=rule_id)
        mapping.active = not mapping.active
        mapping.save()
        return HttpResponseRedirect(reverse("setting"))
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
def new_plugin_setting(request, rule_id, plugin_id,
                   template_name='base/new_plugin_setting.html',
                   extra_context={}):
    """
    Some plugins have configuration and the configuration can be different for
    each rule.
    """

    if system_settings.NEW_SYSTEM:
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
