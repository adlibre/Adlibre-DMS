"""
Module: Document Index form fields producer
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""
from django.conf import settings
from django import forms
from mdt_manager import MetaDataTemplateManager


def get_mdts_for_docrule(docrule_id):
    """
    Generates list of form fields for document.
    Uses MDT's for docrule to list form fields.
    """
    mdt_manager = MetaDataTemplateManager()
    mdt_manager.docrule_id = docrule_id
    mdts_dict = mdt_manager.get_mdts_for_docrule(docrule_id)
    # there is at least 1 MDT exists
#    if settings.DEBUG and not mdts_dict=='error':
#        print mdts_dict
    return mdts_dict

def render_fields_from_docrules(mdts_dict, init_dict=None):
    """
    Create dictionary of additional fields for form, according to MDT's provided.
    Takes optional values dict to init prepopulated fields.
    """
    form_fields_list = {}
    if not init_dict:
        init_dict = {}
    counter = 0
    for mdt_key, mdt_value in mdts_dict.iteritems():
        #print mdt_value['fields']
        if mdt_value["fields"]:
            for field_key, field_value in mdt_value['fields'].iteritems():
                #print field_value
                form_field = None
                if field_value["type"]==u'integer':
                    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
                        # Has initial value
                        form_field = forms.IntegerField(label=field_value["field_name"], help_text=field_value["description"], initial=int(init_dict[unicode(counter)]))
                    else:
                        # Blank field
                        form_field = forms.IntegerField(label=field_value["field_name"], help_text=field_value["description"])
                if field_value["type"]==u'string':
                    max_length=250
                    try:
                        max_length = field_value["length"]
                    except: pass
                    if unicode(counter) in init_dict and init_dict[unicode(counter)]:
                        # Has initial value
                        form_field = forms.CharField(label=field_value["field_name"], help_text=field_value["description"], max_length=max_length, initial=init_dict[unicode(counter)])
                    else:
                        # Blank field
                        form_field = forms.CharField(label=field_value["field_name"], help_text=field_value["description"], max_length=max_length)
                if field_value["type"]==u'date':
                    # TODO: add initial data population ability to DATE field type
                    form_field = forms.DateField(label=field_value["field_name"], help_text=field_value["description"])
                # Setting additional field name (required to use for parsing in future)
                form_field.field_name = field_value["field_name"]
                form_fields_list[counter] = form_field
                counter += 1
    return form_fields_list