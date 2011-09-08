import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from plugins import models

class AdlibreTestCase(TestCase):
    fixtures = ['initial_data.json',]
    
    def _fixture_setup(self, *args, **kwargs):
        #dirty hack to have "our" plugins with correct ids, so that mappings had correct plugin relations
        models.PluginPoint.objects.all().delete()
        models.Plugin.objects.all().delete()
        #dirty hack ends
        super(AdlibreTestCase, self)._fixture_setup(*args, **kwargs)
        try:
            call_command('import_documents', 
                        os.path.join(settings.FIXTURE_DIRS[0], 'testdata'), silent = True )
        except IndexError:
            pass