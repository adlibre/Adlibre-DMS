from django.contrib import admin
from models import DocumentTypeRule

class DocumentTypeRuleAdmin(admin.ModelAdmin):
    list_display = ('doccode_id','title', 'regex', 'split_string', 'no_doccode', 'active', 'description', 'sequence_last')
    exclude = ('sequence_last',) # if changed in the deployment will produce errors.

admin.site.register(DocumentTypeRule, DocumentTypeRuleAdmin)