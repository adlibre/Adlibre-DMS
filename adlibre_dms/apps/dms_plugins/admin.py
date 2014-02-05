from django.contrib import admin
from dms_plugins.models import DoccodePluginMapping


class DoccodePluginMappingAdmin(admin.ModelAdmin):
    list_display = ('doccode', 'active', )

admin.site.register(DoccodePluginMapping, DoccodePluginMappingAdmin)
