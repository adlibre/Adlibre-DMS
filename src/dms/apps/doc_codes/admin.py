from django.contrib import admin
from models import DoccodeModel

class DoccodeModelAdmin(admin.ModelAdmin):
    list_display = ('doccode_id','title', 'regex', 'split_string', 'no_doccode', 'active', 'description' )

admin.site.register(DoccodeModel, DoccodeModelAdmin)