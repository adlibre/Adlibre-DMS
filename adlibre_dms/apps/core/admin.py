"""
Module: DMS Auth User Django Admin Overrides

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Andrew Cutler
Desc: Customise auth user admin to show is_active.

TODO: Show user groups
"""

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from models import CoreConfiguration


class CoreConfigurationAdmin(admin.ModelAdmin):
    pass


def delete_without_warning(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()
delete_without_warning.short_description = "Delete Sessions without warning"


class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()
    list_display = ['session_key', '_session_data', 'expire_date']
    actions = [delete_without_warning]
admin.site.register(Session, SessionAdmin)

UserAdmin.list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(CoreConfiguration, CoreConfigurationAdmin)