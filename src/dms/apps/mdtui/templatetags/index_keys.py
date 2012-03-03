"""
Module: Document Type Rules Model for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import template
from doc_codes.models import DocumentTypeRuleManagerInstance
register = template.Library()

@register.tag(name="get_key_li_item")
def do_key_li_item(parser, token):
    """
    converts search/index form results dict into more readable format.
    Useful for rendering search/indexing form request.
    """
    try:
        # splitings args provided
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
            if item == u'date':
                item = u'Creation Date'
            if item == u'description':
                item = u'Description'
            if item == u'docrule_id':
                item = u'Document Type'
                id = value
                docrule = DocumentTypeRuleManagerInstance.get_docrule_by_id(id)
                value = docrule.get_title()
            resp_string = unicode(item)+u': '+unicode(value)
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
        # splitings args provided
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
            docrule = DocumentTypeRuleManagerInstance.get_docrule_by_id(item)
            value = docrule.get_title()
            return value
        except template.VariableDoesNotExist:
            return ''

@register.tag(name="get_sec_key_for_doc")
def do_sec_key_for_doc_mdtkey(parser, token):
    """
    Returns Secondary Key for this document to populate Search metadata Key's results.
    """
    try:
        # splitings args provided
        tag_name, keys_dict, mdt_dict, key_item = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly two arguments" % token.contents.split()[0])
    return ProvideSecKey(keys_dict, mdt_dict, key_item)

class ProvideSecKey(template.Node):
    def __init__(self, keys_dict, mdt_dict, key_item):
        self.keys_dict = template.Variable(keys_dict)
        self.mdt_dict = template.Variable(mdt_dict)
        self.key_item = template.Variable(key_item)

    def render(self, context):
        try:
            key_item = self.key_item.resolve(context)
            mdt_dict = self.mdt_dict.resolve(context)
            keys_dict = self.keys_dict.resolve(context)
            
            # TODO: DEVELOP THIS FEATURE

            # COMPLEX RENDERING!
            # we need to count calls here. How many calls mean rendering of key number.
            # then check with 'mdts' list that is in the context if this is a proper position.
            # return mdt_dict[key_item] or '' if no key for this doc exist.

            return mdt_dict[key_item]
        except template.VariableDoesNotExist:
            return ''