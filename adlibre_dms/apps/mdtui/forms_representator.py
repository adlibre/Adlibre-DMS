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

from core.models import DocumentTypeRule
from mdt_manager import MetaDataTemplateManager
from security import list_permitted_docrules_pks
from security import list_permitted_docrules_qs

SEARCH_STRING_REPR = {
    'field_label_from': u' From',
    'field_label_to': u' To',
    'id_from': u'_from',
    'id_to': u'_to',
    'MDT_SEARCH': u"Custom Search",
}

log = logging.getLogger('dms.mdtui.views')


def get_mdts_for_docrule(docrule_id):
    """
    Generates list of form fields for document.
    Uses MDT's for docrule to list form fields.
    """
    log.debug("Getting MDT's from CouchDB")
    if docrule_id.__class__.__name__ == 'int':
        docrule_id = str(docrule_id)
    mdt_manager = MetaDataTemplateManager()
    mdt_manager.docrule_id = docrule_id
    mdts_dict = mdt_manager.get_mdts_for_docrule(docrule_id)
    # there is at least 1 MDT exists
    if not mdts_dict=='error':
        log.debug("Got MDT's: %s" % mdts_dict)
    else:
        log.debug("No MDT's found")
    return mdts_dict


def render_choice_field(counter, field_value, init_dict):
    """Form fields renderer for data type CHOICE

    @param counter: number of field in a form
    @param field_value: additional field data to render a field
    @param init_dict: is a set of optional initial values"""
    mdt_choices = field_value['choices']
    choices = zip(range(mdt_choices.__len__()), mdt_choices)
    initial_choice = ('', '')
    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
        # Has initial value
        choice_value = init_dict[unicode(counter)]
        for choice in choices:
            if choice[1] == choice_value:
                initial_choice = choice
    return forms.ChoiceField(
        choices,
        label=field_value["field_name"],
        help_text=field_value["description"],
        initial=initial_choice
    )


def render_string_field(counter, field_value, init_dict):
    """Form fields renderer for data type STRING

    @param counter: number of field in a form
    @param field_value: additional field data to render a field
    @param init_dict: is a set of optional initial values"""
    if "length" in field_value.iterkeys():
        max_length = field_value["length"]
    else:
        max_length = 100
    initial = None
    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
        # Has initial value
        initial = init_dict[unicode(counter)]
    return forms.CharField(
        label=field_value["field_name"],
        help_text=field_value["description"],
        max_length=max_length,
        initial=initial
    )


def render_integer_field(counter, field_value, init_dict):
    """Form fields renderer for data type INTEGER

    @param counter: number of field in a form
    @param field_value: additional field data to render a field
    @param init_dict: is a set of optional initial values"""
    initial = None
    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
        # Has initial value
        initial = init_dict[unicode(counter)]
    return forms.IntegerField(
        label=field_value["field_name"],
        help_text=field_value["description"],
        initial=initial
    )


def render_date_field(counter, field_value, init_dict, label=False):
    # Normally adding only one field for indexing
    initial = None
    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
        # Has initial value
        initial = init_dict[unicode(counter)]
    if not label:
        label = field_value["field_name"]
    return forms.DateField(
        label=label,
        help_text=field_value["description"],
        initial=initial
    )


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
                if field_value["type"] == u'choice':
                    form_field = render_choice_field(counter, field_value, init_dict)
                if field_value["type"] == u'integer':
                    form_field = render_integer_field(counter, field_value, init_dict)
                if field_value["type"] == u'string':
                    form_field = render_string_field(counter, field_value, init_dict)
                if field_value["type"] == u'date':
                    if not search:
                        form_field = render_date_field(counter, field_value, init_dict)
                    else:
                        from_label = field_value["field_name"] + SEARCH_STRING_REPR['field_label_from']
                        to_label = field_value["field_name"] + SEARCH_STRING_REPR['field_label_to']
                        # Rendering and adding From field first
                        form_field = render_date_field(counter, field_value, init_dict, from_label)
                        form_field.field_name = field_value["field_name"] + SEARCH_STRING_REPR['field_label_from']
                        form_fields_list[unicode(counter) + SEARCH_STRING_REPR['id_from']] = form_field
                        # rendering To field and processing as all other fields
                        form_field = render_date_field(counter, field_value, init_dict, to_label)
                if "uppercase" in field_value.iterkeys():
                    if field_value["uppercase"] == "yes":
                        form_field.is_uppercase = True
                # Setting additional field name (required to use for parsing in templates)
                if search and field_value["type"] == u'date':
                    form_field.field_name = field_value["field_name"] + SEARCH_STRING_REPR['field_label_to']
                    form_fields_list[unicode(counter) + SEARCH_STRING_REPR['id_to']] = form_field
                else:
                    form_field.field_name = field_value["field_name"]
                    form_fields_list[counter] = form_field
                counter += 1
    log.debug('Rendered dynamic fields to add to form: %s' % form_fields_list)
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


def make_document_type_select(user=None):
    """Returns proper set of docrules for a given request.user"""
    docrules_queryset = ()
    if user:
        if not user.is_superuser:
            docrules_queryset = list_permitted_docrules_qs(user)
        else:
            docrules_queryset = DocumentTypeRule.objects.filter(active=True)
    return docrules_queryset


def make_document_type_select_form(user=None, required=True, docrule_initial=None):
    """
    Special method to construct custom DocumentTypeSelectForm object

    with list of DocumentTypeRule() limited with user permissions
    """
    # Check for user permissions and build queryset for form based on that.
    if user:
        if not user.is_superuser:
            docrules_queryset = list_permitted_docrules_qs(user)
        else:
            docrules_queryset = DocumentTypeRule.objects.all()

    # Build a form with provided queryset of DocumentTypeRules.
    class DocumentTypeSelectForm(forms.Form):
        docrule = forms.ModelChoiceField(
            queryset=docrules_queryset,
            label="Document Type",
            required=required,
            initial=docrule_initial
        )
    return DocumentTypeSelectForm


def make_mdt_select_form(user=None, required=True):
    """
    Special method to construct custom MDTSearchSelectForm
    suggests MDT's for search that only restricted by user Docrule permissions.
    E.g.:
    'MDT1' is shown in MDTSearchSelectForm only if:
    'MDT1' has connected 'docrule1' AND 'user', that is provided to method,
    has permission to interact with this DocumentTypeRule ('docrule1' in our case).
    """
    # Fetching all mdts that have more than 1 docrule
    mdt_m = MetaDataTemplateManager()
    all_mdts = {}
    try:
        couch_mdts = mdt_m.get_all_mdts()
        # Filtering with more than 1 docrule count
        if couch_mdts:
            for mdt_id, mdt in couch_mdts.iteritems():
                mdt_docrules = mdt['docrule_id']
                if mdt_docrules.__len__() > 1:
                    all_mdts[mdt_id] = mdt
    except RequestError:
        # No CouchDB
        pass
    filtered_mdts = {}
    # Filtering MDT's displaying only permitted ones for provided user
    if not user.is_superuser and all_mdts:
        allowed_docrules_pks = list_permitted_docrules_pks(user)
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
        mdt = forms.ChoiceField(choices=mdt_choices, label=SEARCH_STRING_REPR['MDT_SEARCH'], required=required)

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


def construct_edit_indexes_data(mdts, db_info):
    """ Method to indexes dictionary with new indexes according to existing MDTS."""
    indexes_dict = {'description': db_info['description']}
    # Finding key in MDT's and appending it to the form.
    counter = 0
    for mdt in mdts.itervalues():
        # Sort fields, like render_fields_from_docrules method does
        sorted_fields = mdt['fields'].items()
        sorted_fields.sort()
        for field_key, field in sorted_fields:
            # Fail gracefully if no index for this MDT exists in DB
            # Thus enabling us to add new MDTs for documents
            # without creating serious bugs in editing document
            if 'mdt_indexes' in db_info:
                # We're initialising from document data
                try:
                    indexes_dict[str(counter)] = db_info['mdt_indexes'][field['field_name']]
                except:
                    pass
            else:
                # We're initialising from pre-stored data
                try:
                    indexes_dict[str(counter)] = db_info[field['field_name']]
                except:
                    pass
            counter += 1
    return indexes_dict