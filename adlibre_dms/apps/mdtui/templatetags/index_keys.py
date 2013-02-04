"""
Module: Template rendering helpers for MDTUI

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import datetime

from django import template
from django.conf import settings

from doc_codes.models import DocumentTypeRuleManager

register = template.Library()

@register.tag(name="get_key_li_item")
def do_key_li_item(parser, token):
    """
    converts search/index form results dict into more readable format.

    Useful for rendering search/indexing form request.
    """
    try:
        # splitting args provided
        tag_name, keys_dict, key_item = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly two arguments" % token.contents.split()[0])
    return ProvideLiElement(keys_dict, key_item)

class ProvideLiElement(template.Node):
    def __init__(self, keys_dict, key_item):
        self.keys_dict = template.Variable(keys_dict)
        self.key_item = template.Variable(key_item)

    def render(self, context):
        try:
            item = self.key_item.resolve(context)
            dict = self.keys_dict.resolve(context)
            value = dict[item]
            # Special rendering for 'date' variable in search
            if item == u'date':
                date = dict[u'date']
                if u'end_date' in dict:
                    end_date = dict[u'end_date']
                    item = u'Creation Date: (from: ' + unicode(date) + u' to: ' + unicode(end_date) + u')'
                    return item
                else:
                    # Normal rendering for indexes
                    item = u'Creation Date'
            if item == u'description':
                item = u'Description'
            if item == u'docrule_id':
                item = u'Document Type'
                id = value
                dman = DocumentTypeRuleManager()
                docrule = dman.get_docrule_by_id(id)
                value = docrule.get_title()
            if not value.__class__.__name__ == 'tuple':
                resp_string = unicode(item) + u': ' + unicode(value)
            else:
                resp_string = unicode(item) + u': (from: ' + unicode(value[0]) + u' to: ' + unicode(value[1]) + u')'
            return resp_string
        except template.VariableDoesNotExist:
            return ''

@register.tag(name="get_docrule_name_by_id")
def do_docrule_name_by_id(parser, token):
    """
    Provides Document Rule Name instead of Document Rule ID, provided

    Uses standard DocruleManager method without making any db requests.
    """
    try:
        # splitting args provided
        tag_name, key_item = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly one argument" % token.contents.split()[0])
    return ConvertDocrule(key_item)

class ConvertDocrule(template.Node):
    def __init__(self, key_item):
        self.key_item = template.Variable(key_item)

    def render(self, context):
        try:
            item = self.key_item.resolve(context)
            try:
                int(item)
            except: return 'None'
            dman = DocumentTypeRuleManager()
            docrule = dman.get_docrule_by_id(item)
            value = docrule.get_title()
            value = unicode(value).capitalize()
            return value
        except template.VariableDoesNotExist:
            return ''

@register.tag(name="get_sec_key_for_doc")
def do_sec_key_for_doc_mdtkey(parser, token):
    """
    Returns Secondary Key for this document

    to populate Search metadata Key's results.
    """
    try:
        # splitting args provided
        tag_name, doc_keys_dict, key_item = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly 2 arguments" % token.contents.split()[0])
    return ProvideSecKey(doc_keys_dict, key_item)

class ProvideSecKey(template.Node):
    def __init__(self, doc_keys_dict, key_item):
        self.doc_keys_dict = template.Variable(doc_keys_dict)
        self.key_item = template.Variable(key_item)

    def render(self, context):
        try:
            key_item = self.key_item.resolve(context)
            doc_keys_dict = self.doc_keys_dict.resolve(context)
            try:
                value = doc_keys_dict[key_item]
            except:
                value = ''
            # Matching/converting from CouchDB time format
            try:
                value = datetime.datetime.strftime(value, settings.DATE_FORMAT)
            except TypeError:
                pass
            return value
        except template.VariableDoesNotExist:
            return ''

@register.tag(name="get_form_id_for_key")
def get_field_id_from_form_by_name(parser, token):
    """
    Returns Form #id for Secondary Key field provided.

    Uses Indexes form to retrieve dependency.
    """
    try:
        # splitting args provided
        tag_name, form, key_item = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly 2 arguments" % token.contents.split()[0])
    return ProvideIDForSecKey(form, key_item)

class ProvideIDForSecKey(template.Node):
    def __init__(self, form, key_item):
        self.form = template.Variable(form)
        self.key_item = template.Variable(key_item)

    def render(self, context):
        try:
            key_item = self.key_item.resolve(context)
            form = self.form.resolve(context)
            try:
                for field_id, field in form.fields.iteritems():
                    try:
                        #print field.field_name
                        if field.field_name == key_item:
                            return "#id_"+str(field_id)
                    except AttributeError:
                        pass
            except:
                return ''
        except template.VariableDoesNotExist:
            return ''

@register.filter
def field_type(field):
    """
    Returns field type in 'str'
    """
    return field.field.__class__.__name__

@register.simple_tag(takes_context=True)
def get_used_in_search_mdt(context):
    """Used to display Search MDT names relation in heading.

    E.g. Search Adlibre Invoices
    Retrieves MDT name from request sessio contest.

    """
    try:
        session = context['request'].session
        result = u''
        if session:
            for mdt in session['mdts']:
                result += unicode(session['mdts'][mdt]['mdt_id']).capitalize()
        return result
    except Exception, e:
        print e
        return ''
        pass

@register.simple_tag(takes_context=True)
def set_field_value(context, field_value):
    """populates variable into a context"""
    if field_value:
        context['field_value'] = field_value
    else:
        context['field_value'] = ''
    return ''

@register.simple_tag(takes_context=True)
def set_key(context, key):
    """populates variable into a context"""
    if key:
        context['key'] = key
    else:
        context['key'] = ''
    return ''

@register.filter
def choice_id(choice):
    """
    Returns Choice type field's choice id for form rendering
    """
    try:
        resp = choice[0]
    except IndexError:
        resp = ''
        pass
    return resp

@register.filter
def choice_name(choice):
    """
    Returns Choice type field's choice Name (Text) for form rendering
    """
    try:
        resp = choice[1]
    except IndexError:
        resp = ''
        pass
    return resp