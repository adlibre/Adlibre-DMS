
from django.contrib import admin

from models import FileShare



class FileShareAdmin(admin.ModelAdmin):
    list_display = ('hashcode', 'sharefile')
                    
                    
                    
admin.site.register(FileShare, FileShareAdmin)
