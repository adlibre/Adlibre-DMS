"""
Module: API Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""
import json
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from plugins import models

from doc_codes import DoccodeManagerInstance
from dms_plugins.models import DoccodePluginMapping

from base_test import AdlibreTestCase

# TODO: Create a test document code, and a set of test documents at the start of test
"""
Test data
"""
# auth user
username = 'admin'
password = 'admin'

documents = ('ADL-1111', 'ADL-1234', 'ADL-2222',)
documents_missing = ()

documents_hash = [
    ('abcde111', 'cad121990e04dcd5631a9239b3467ee9'),
    ('abcde123', 'bc3c5035805bb8098e5c164c5e1826da'),
    ('abcde222', 'ba7e656a1288181cdcf676c0d719939e'),
    ]

rules = (1, 2,)
rules_missing = ()

# no doccode
no_doccode_name = "test_no_doccode"
adl_invoice_name = "ADL-1985"

#tagging
test_tag = 'test_tag'

# TODO: Write a test that checks these methods for ALL doctypes that are currently installed :)

class MiscTest(AdlibreTestCase):
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

    def test_api_files(self):
        doccode = DoccodeManagerInstance.get_doccode_by_name('Adlibre Invoices')
        mapping = DoccodePluginMapping.objects.get(doccode = doccode.get_id())
        url = reverse("api_file_list", kwargs = {'id_rule': mapping.pk})
        response = self.client.get(url)
        self.assertContains(response, 'ADL-1234')

    def test_api_file(self):
        self.client.login(username=username, password=password)
        f = documents_hash[0][0]
        doc_hash = documents_hash[0][1]
        response1 = self._upload_file(f)
        revision = 1
        url = reverse('api_file') + '?filename=%s.pdf&r=%s&h=%s' % (f, revision, doc_hash)
        response = self.client.get(url)
        self.assertContains(response, '', status_code = 200)

    def test_api_fileinfo(self):
        self.client.login(username = username, password = password)
        for f in documents:
            url = reverse('api_file_info') + '?filename=%s' % f
            response = self.client.get(url)
            data = json.loads(response.content)
            if not 'document_name' in data or not (data['document_name'] == f):
                raise self.failureException('Invalid response: %s' % response.content)

    def test_api_rename(self):
        #login
        self.client.login(username = username, password = password)
        #upload no doccode
        response = self._upload_file(no_doccode_name)
        self.assertContains(response, '', status_code = 200)
        #do rename
        url = reverse('api_file')
        data = {'new_name': adl_invoice_name, 'filename': no_doccode_name + ".pdf"}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        #fetch renamed file
        url = reverse('api_file') + '?filename=%s.pdf' % adl_invoice_name
        response = self.client.get(url)
        self.assertContains(response, '', status_code = 200)

    def test_api_tags(self):
        #login
        self.client.login(username = username, password = password)
        #upload file
        filename = documents[0]
        response = self._upload_file(filename)
        self.assertContains(response, '', status_code = 200)
        #remove tag
        url = reverse('api_file')
        data = {'filename': filename, 'remove_tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        #check that we don't have tag
        url = reverse('api_file_info')
        data = {'filename': filename}
        response = self.client.get(url, data)
        self.assertNotContains(response, test_tag, status_code = 200)
        #set tags
        url = reverse('api_file')
        data = {'filename': filename, 'tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        #check that we have tag
        url = reverse('api_file_info')
        data = {'filename': filename}
        response = self.client.get(url, data)
        self.assertContains(response, test_tag, status_code = 200)

    def _upload_file(self, f):
        url = reverse('api_file')
        self.client.login(username=username, password=password)
        # do upload
        file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', f + '.pdf')
        data = { 'file': open(file, 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_files(self):
        for f in documents:
            response = self._upload_file(f)
            self.assertContains(response, f, status_code = 200)

    def _test_delete_documents(self): # disabled
        for f in documents:
            url = reverse('api_file') + '?filename=' + f + '.pdf'
            self.client.login(username=username, password=password)
            response = self.client.delete(url)
            self.assertContains(response, '', status_code = 204)


    def test_get_rev_count(self):
        for f in documents:
            url = reverse('api_revision_count', kwargs = {'document': f})
            self.client.login(username=username, password=password)
            # do upload
            self._upload_file(f)
            response = self.client.get(url)
            if not response.content.isdigit():
                raise self.failureException('Invalid response: %s' % response.content)


    def test_get_bad_rev_count(self):
        url = reverse('api_revision_count', kwargs = {'document': 'sdfdsds42333333333333333333333333432423'})
        response = self.client.get(url)
        self.assertContains(response, 'Bad Request', status_code = 400)


