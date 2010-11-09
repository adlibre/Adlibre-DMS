
from django.contrib import admin

from models import Rule


def rule_doc(obj):
    return ("%s" % (obj.get_doccode().name))
rule_doc.short_description = 'Document Code'


class RuleAdmin(admin.ModelAdmin):
    list_display = (rule_doc,)




admin.site.register(Rule, RuleAdmin)

