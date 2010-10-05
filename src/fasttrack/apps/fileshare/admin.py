
from django.contrib import admin

from models import Rule



class RuleAdmin(admin.ModelAdmin):
    list_display = ('doccode',)



admin.site.register(Rule, RuleAdmin)

