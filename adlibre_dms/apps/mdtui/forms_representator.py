"""
Module: Document Index form fields producer

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging
import datetime

from django import forms
from django.conf import settings

from restkit.client import RequestError

from mdt_manager import MetaDataTemplateManager
from doc_codes.models import DocumentTypeRule

SEARCH_STRING_REPR = {
    'field_label_from': u' From',
    'field_label_to': u' To',
    'id_from': u'_from',
    'id_to': u'_to',
    }

log = logging.getLogger('dms.mdtui.views')

def get_mdts_for_docrule(docrule_id):
    """
    Generates list of form fields for document.
    Uses MDT's for docrule to list form fields.
    """
    log.debug("Getting MDT's from CouchDB")
    mdt_manager = MetaDataTemplateManager()
    mdt_manager.docrule_id = docrule_id
    mdts_dict = mdt_manager.get_mdts_for_docrule(docrule_id)
    # there is at least 1 MDT exists
    if not mdts_dict=='error':
        log.debug("Got MDT's: %s" % mdts_dict)
    else:
        log.debug("No MDT's found")
    return mdts_dict

def render_fields_from_docrules(mdts_dict, init_dict=None, search=False):
    """
    Create dictionary of additional fields for form,

    according to MDT's provided.
    Takes optional values dict to init prepopulated fields.
    """
    log.debug('Rendering fields for docrules: "%s", init_dict: "%s", search: "%s"'% (mdts_dict, init_dict, search))
    form_fields_list = {}
    if not init_dict:
        init_dict = {}
    counter = 0
    for mdt_key, mdt_value in mdts_dict.iteritems():
        #print mdt_value['fields']
        if mdt_value["fields"]:
            # Sort fields
            sorted_fields = mdt_value['fields'].items()
            sorted_fields.sort()
            for field_key, field_value in sorted_fields:
                form_field = None
                if field_value["type"]==u'integer':
                    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
                        # Has initial value
                        form_field = forms.IntegerField(label=field_value["field_name"], help_text=field_value["description"], initial=init_dict[unicode(counter)])
                    else:
                        # Blank field
                        form_field = forms.IntegerField(label=field_value["field_name"], help_text=field_value["description"])
                if field_value["type"]==u'string':
                    try:
                        max_length = field_value["length"]
                    except KeyError:
                        max_length=100
                    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
                        # Has initial value
                        form_field = forms.CharField(label=field_value["field_name"], help_text=field_value["description"], max_length=max_length, initial=init_dict[unicode(counter)])
                    else:
                        # Blank field
                        form_field = forms.CharField(label=field_value["field_name"], help_text=field_value["description"], max_length=max_length)
                if field_value["type"]==u'date':
                    if not search:
                        # Normally adding only one field for indexing
                        if unicode(counter) in init_dict and init_dict[unicode(counter)]:
                            # Has initial value
                            form_field = forms.DateField(label=field_value["field_name"], help_text=field_value["description"], initial=init_dict[unicode(counter)])
                        else:
                            # Blank field
                            form_field = forms.DateField(label=field_value["field_name"], help_text=field_value["description"])
                    else:
                        from_label = field_value["field_name"] + SEARCH_STRING_REPR['field_label_from']
                        to_label = field_value["field_name"] + SEARCH_STRING_REPR['field_label_to']
                        # Normally adding only from/to fields for indexing
                        if unicode(counter) in init_dict and init_dict[unicode(counter)]:
                            # Has initial value
                            form_field = forms.DateField(label=from_label, help_text=field_value["description"], initial=init_dict[unicode(counter)])
                            # Adding first field (From)
                            form_field.field_name = field_value["field_name"] + SEARCH_STRING_REPR['field_label_from']
                            form_fields_list[unicode(counter) + SEARCH_STRING_REPR['id_from']] = form_field
                            counter += 1
                            # Second field (To)
                            form_field = forms.DateField(label=to_label, help_text=field_value["description"], initial=init_dict[unicode(counter)])
                        else:
                            # Blank field
                            form_field = forms.DateField(label=from_label, help_text=field_value["description"])
                            # Adding first field (From)
                            form_field.field_name = field_value["field_name"] + SEARCH_STRING_REPR['field_label_from']
                            form_fields_list[unicode(counter) + SEARCH_STRING_REPR['id_from']] = form_field
                            # Second field (To)
                            form_field = forms.DateField(label=to_label, help_text=field_value["description"])
                if "uppercase" in field_value.iterkeys():
                    if field_value["uppercase"]=="yes":
                        form_field.is_uppercase = True
                    # Setting additional field name (required to use for parsing in templates)
                if search and field_value["type"]==u'date':
                    form_field.field_name = field_value["field_name"] + SEARCH_STRING_REPR['field_label_to']
                    form_fields_list[unicode(counter) + SEARCH_STRING_REPR['id_to']] = form_field
                else:
                    form_field.field_name = field_value["field_name"]
                    form_fields_list[counter] = form_field
                counter += 1
    log.debug('Rendered dynamic fields to add to form: ', form_fields_list)
    return form_fields_list

def setFormFields(fm, kwds):
    """
    Set the fields in the dynamic form
    """
    keys = kwds.keys()
    keys.sort()
    for k in keys:
        fm.fields[k] = kwds[k]

def setFormData(fm, kwds):
    """
    Set the data to include in the form's dynamic fields
    """
    keys = kwds.keys()
    keys.sort()

    fm.is_valid()
    for k in keys:
        fm.data[k] = kwds[k]
        try:
            fm.initial[k] = int(kwds[k])
        except ValueError:
            try:
                dt = datetime.datetime.strptime(kwds[k], settings.DATE_FORMAT)
                fm.initial[k] = dt
            except ValueError:
                try:
                    fm.initial[k] = kwds[k]
                except ValueError:
                        pass

def make_mdt_select_form(user=None):
    """
    Special method to construct custom MDTSearchSelectForm
    suggests MDT's for search that only restricted by user Docrule permissions.
    E.g.:
    'MDT1' is shown in MDTSearchSelectForm only if:
    'MDT1' has connected 'docrule1' AND 'user', that is provided to method,
    has permission to interact with this DocumentTypeRule ('docrule1' in our case).
    """
    mdt_m = MetaDataTemplateManager()
    try:
        all_mdts = mdt_m.get_all_mdts()
    except RequestError:
        all_mdts = {}
        pass
    filtered_mdts = {}
    # Filtering MDT's displaying only permitted ones for provided user
    if not user.is_superuser:
        # Filtering Document Type Rules for user
        perms = user.user_permissions.all()
        allowed_docrules_names = []
        for permission in perms:
            if permission.content_type.name=='document type':
                if not permission.codename in allowed_docrules_names:
                    allowed_docrules_names.append(permission.codename)
        for group in user.groups.all():
            for permission in group.permissions.all():
                if permission.content_type.name=='document type':
                    if not permission.codename in allowed_docrules_names:
                        allowed_docrules_names.append(permission.codename)
        docrules_queryset = DocumentTypeRule.objects.filter(title__in=allowed_docrules_names)
        # Getting list of PKs of allowed Document Type Rules.
        allowed_docrules_pks = []
        if docrules_queryset:
            for rule in docrules_queryset:
                allowed_docrules_pks.append(unicode(rule.pk))

        # Filtering all_mdts by only allowed ones
        for mdt in all_mdts:
            mdt_docrules = all_mdts[mdt]['docrule_id']
            for docrule_id in mdt_docrules:
                if docrule_id in allowed_docrules_pks:
                    filtered_mdts[mdt] = all_mdts[mdt]
    # listing mdts to display in form by number, mdt_id
    if filtered_mdts:
        mdt_choices = [(mdt, all_mdts[mdt]['mdt_id']) for mdt in filtered_mdts.iterkeys()]
    else:
        mdts_list = [mdt for mdt in all_mdts.iterkeys()]
        mdt_choices = [(mdt, all_mdts[mdt]['mdt_id']) for mdt in mdts_list]
    mdt_choices.sort()

    # Constructing form
    class MDTSelectForm(forms.Form):
        mdt = forms.ChoiceField(choices=mdt_choices, label="Meta Data Template")

    return MDTSelectForm

def get_mdt_from_search_mdt_select_form(mdt_ids, form):
    """
    Method extracts MDT name from form (that has mdt names already)

    Economises 1 CouchDB + DB requests this way.
    """
    names_list = []
    ids_list = form.base_fields['mdt'].choices
    for choice in ids_list:
        if choice[0] in mdt_ids:
            names_list.append(choice[1])
    return names_list
