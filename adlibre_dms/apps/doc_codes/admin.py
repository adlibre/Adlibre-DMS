from django.contrib import admin
from models import DocumentTypeRule

class DocumentTypeRuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'pk', 'regex', 'split_string', 'no_doccode', 'active', 'description', 'sequence_last')

admin.site.register(DocumentTypeRule, DocumentTypeRuleAdmin)
