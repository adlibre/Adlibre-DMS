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