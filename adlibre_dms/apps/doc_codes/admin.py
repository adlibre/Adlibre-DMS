from django.contrib import admin
from doc_codes.models import DocumentTypeRule
from doc_codes.models import DocumentTypeRulePermission
from django.contrib.auth.models import Permission, ContentType


class DocumentTypeRuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'pk', 'regex', 'split_string', 'active', 'description', 'sequence_last')


class DocumentTypeRulePermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'pk']

    def queryset(self, request):
        """Faking queryset"""
        super(DocumentTypeRulePermissionAdmin, self).queryset(request)

        content_type, created = ContentType.objects.get_or_create(
            app_label='rule',
            model='',
            name='document type'
        )
        qs = Permission.objects.filter(content_type=content_type)
        return qs

    def name(self, item):
        """Dummy method action to display property in a list display"""
        return item

    def codename(self, item):
        """Dummy method action to display property in a list display"""
        return item

    def content_type(self, item):
        """Dummy method action to display property in a list display"""
        return item

admin.site.register(DocumentTypeRule, DocumentTypeRuleAdmin)
admin.site.register(DocumentTypeRulePermission, DocumentTypeRulePermissionAdmin)
admin.site.register(Permission)
