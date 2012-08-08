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

UserAdmin.list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)