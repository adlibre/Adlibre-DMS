"""
Module: DMS Core admin functions

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Andrew Cutler
Desc:
    Customise auth user admin to show is_active.
    Document Type Rule management.
    DMS configuration Management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth.models import Permission, ContentType

from models import CoreConfiguration
from models import DocumentTypeRule
from models import DocumentTypeRulePermission
from models import DocTags


def delete_without_warning(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()
delete_without_warning.short_description = "Delete Sessions without warning"


class CoreConfigurationAdmin(admin.ModelAdmin):
    pass


class DocumentTypeRuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'pk', 'regex', 'split_string', 'active', 'description', 'sequence_last')


class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()
    list_display = ['session_key', '_session_data', 'expire_date']
    actions = [delete_without_warning]
admin.site.register(Session, SessionAdmin)


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


UserAdmin.list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active',)

admin.site.register(DocumentTypeRule, DocumentTypeRuleAdmin)
admin.site.register(DocumentTypeRulePermission, DocumentTypeRulePermissionAdmin)
admin.site.register(Permission)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(CoreConfiguration, CoreConfigurationAdmin)
admin.site.register(DocTags)