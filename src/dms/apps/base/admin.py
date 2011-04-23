"""
Module: Base Django Admin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.contrib import admin

from models import Rule, PluginRule


def rule_doc(obj):
    return ("%s" % (obj.get_doccode().name))
rule_doc.short_description = 'Document Code'


class RuleAdmin(admin.ModelAdmin):
    list_display = (rule_doc, 'active')


admin.site.register(Rule, RuleAdmin)

admin.site.register(PluginRule)
