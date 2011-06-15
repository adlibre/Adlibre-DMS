"""
Module: API Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from plugins import models

from doc_codes import DoccodeManagerInstance
from dms_plugins.models import DoccodePluginMapping

# TODO: Create a test document code, and a set of test documents at the start of test
"""
Test data
"""
# auth user
username = 'admin'
password = 'admin'

documents = ('ADL-1111', 'ADL-1234', 'ADL-2222',)
documents_missing = ()

rules = (1, 2,)
rules_missing = ()


# TODO: We need to extend the API to the following
# 1. Return revisions for a given file /api/revisions/ADL-1234.json
# 2. Return meta-data for a given file /api/metadata/ADL-1234.json
# 3. Delete files /api/delete/ADL-1234
# 4. Require authentication for API all actions.



# TODO: Write a test that checks these methods for ALL doctypes that are currently installed :)

class MiscTest(TestCase):

    fixtures = ['test_data.json',]

    def test_api_rule_detail(self):
        doccode = DoccodeManagerInstance.get_doccode_by_name('Test PDFs')
        mapping = DoccodePluginMapping.objects.get(doccode = doccode.get_id())
        #we don't really care if it crashes above, cause that means our database is imperfect
        url = reverse('api_rules_detail', kwargs = {'id_rule': 2, 'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, 'Test PDFs')

    def test_api_rules(self):
        url = reverse('api_rules', kwargs = {'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, 'Test PDFs')

    def test_api_plugins(self):
        url = reverse('api_plugins', kwargs = {'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, 'dms_plugins.workers.storage.local.LocalStoragePlugin')

    def _fixture_setup(self, *args, **kwargs):
        #dirty hack to have "our" plugins with correct ids, so that mappings had correct plugin relations
        models.PluginPoint.objects.all().delete()
        models.Plugin.objects.all().delete()
        #dirty hack ends
        super(MiscTest, self)._fixture_setup(*args, **kwargs)

    def test_api_files(self):
        FILENAME = 'ADL-1234'
        url = '/api/files/1/'
        response = self.client.get(url)
        self.assertContains(response, FILENAME)


    def _upload_file(self, f):
        url = '/api/file/'
        self.client.login(username=username, password=password)
        # do upload
        file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.pdf'
        data = { 'file': open(file, 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_files(self):
        for f in documents:
            response = self._upload_file(f)
            self.assertContains(response, f, status_code = 200)

    def test_delete_documents(self):
        for f in documents:
            url = '/api/file/?filename=' + f + '.pdf'
            self.client.login(username=username, password=password)
            response = self.client.delete(url)
            self.assertContains(response, '', status_code = 204)


    def test_get_rev_count(self):
        for f in documents:
            url = '/api/revision_count/' + f
            self.client.login(username=username, password=password)
            # do upload
            #file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.pdf'
            #data = { 'filename': open(file, 'r'), }
            #response = self.client.post(url, data)
            response = self.client.get(url)
            self.assertContains(response, '')


    def test_get_bad_rev_count(self):
        url = '/api/revision_count/sdfdsds42333333333333333333333333432423'
        response = self.client.get(url)
        self.assertContains(response, 'Bad Request', status_code=400)


