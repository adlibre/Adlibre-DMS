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

from doc_codes.models import DocumentTypeRuleManagerInstance
from dms_plugins.models import DoccodePluginMapping

from adlibre.dms.base_test import DMSTestCase

# TODO: Create a test document code, and a set of test documents at the start of test
"""
Test data
"""


# documents should be added to this list
# if manually added to 'fixtures/testdata' directory,
# or they will be added to project by every test run and left there...
unlisted_files_used = [
    'test_document_template.odt',
    'test_no_doccode.pdf',
    '2011-01-27-1.tif',
    '2011-01-28-12.tif',
    'abcde888.pdf',
    'abcde999.pdf',
    '10001.txt',
    '10006.txt',
    '101.txt',
]

adlibre_invoices_rule_id = 1
documents = ('ADL-0001', 'ADL-0002', 'ADL-1111', 'ADL-1234', 'ADL-2222',)
documents_missing = ()


rules = (1, 2,)
rules_missing = ()

# no doccode
no_doccode_name = "test_no_doccode"
adl_invoice_name = "ADL-1985"
no_doccode_docs = ['ADL-54321', 'ADL-12345', ]

# tagging
test_tag = 'test_tag'

# TODO: Write a test that checks these methods for ALL doctypes that are currently installed :)

class APITest(DMSTestCase):

    def test_00_api_setup(self):
        """
        Load Test Data
        """
        self.loadTestDocuments()

    def test_api_rule_detail(self):
        doccode = DocumentTypeRuleManagerInstance.get_docrule_by_name('Test PDFs')
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
        doccode = DocumentTypeRuleManagerInstance.get_docrule_by_name('Adlibre Invoices')
        mapping = DoccodePluginMapping.objects.get(doccode = doccode.get_id())
        url = reverse("api_file_list", kwargs = {'id_rule': mapping.pk})
        response = self.client.get(url)
        self.assertContains(response, 'ADL-1234')

    def test_api_file(self):
        self.client.login(username=self.username, password=self.password)
        f = self.documents_hash[0][0]
        doc_hash = self.documents_hash[0][1]
        response1 = self._upload_file(f)
        revision = 1
        url = reverse('api_file') + '?filename=%s.pdf&r=%s&h=%s' % (f, revision, doc_hash)
        response = self.client.get(url)
        self.assertContains(response, '', status_code = 200)

    def test_api_fileinfo(self):
        self.client.login(username=self.username, password=self.password)
        for f in documents:
            url = reverse('api_file_info') + '?filename=%s' % f
            response = self.client.get(url)
            data = json.loads(response.content)
            if not 'document_name' in data or not (data['document_name'] == f):
                raise self.failureException('Invalid response: %s' % response.content)

    def test_api_rename(self):
        # Login
        self.client.login(username=self.username, password=self.password)
        # Upload no doccode
        response = self._upload_file(no_doccode_name)
        self.assertContains(response, '', status_code = 200)
        # Do rename
        filename = no_doccode_name + ".pdf"
        url = reverse('api_file') + '?filename=%s' % filename
        data = {'filename': filename, 'new_name': adl_invoice_name,}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        # Fetch renamed file
        url = reverse('api_file') + '?filename=%s.pdf' % adl_invoice_name
        response = self.client.get(url)
        # Fail to fetch old file
        url = reverse('api_file') + '?filename=%s.pdf' % no_doccode_name
        response = self.client.get(url)
        self.assertContains(response, '', status_code = 400)

    def test_api_tags(self):
        #login
        self.client.login(username=self.username, password=self.password)
        #upload file
        filename = documents[0]
        response = self._upload_file(filename)
        self.assertContains(response, '', status_code = 200)
        #remove tag
        url = reverse('api_file') + '?filename=%s' % filename
        data = {'filename': filename, 'remove_tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        #check that we don't have tag
        url = reverse('api_file_info')
        data = {'filename': filename}
        response = self.client.get(url, data)
        self.assertNotContains(response, test_tag, status_code = 200)
        #set tags
        url = reverse('api_file') + '?filename=%s' % filename
        data = {'filename': filename, 'tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        #check that we have tag
        url = reverse('api_file_info')
        data = {'filename': filename}
        response = self.client.get(url, data)
        self.assertContains(response, test_tag, status_code = 200)
        #get all tags for rule, check our tag
        url = reverse('api_tags', kwargs = {'id_rule': adlibre_invoices_rule_id, 'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, test_tag, status_code = 200)

    def _upload_file(self, f):
        url = reverse('api_file')
        self.client.login(username=self.username, password=self.password)
        # do upload
        file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', f + '.pdf')
        data = { 'file': open(file, 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_files(self):
        for f in documents:
            response = self._upload_file(f)
            self.assertContains(response, f, status_code = 200)

    def _delete_documents(self, delete_doc, remain_doc):
        url = reverse('api_file') + '?filename=' + delete_doc + '.pdf'
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(url)
        self.assertContains(response, '', status_code = 204)

        url = reverse('api_file') + '?filename=%s.pdf' % remain_doc
        response = self.client.get(url)
        self.assertContains(response, '', status_code = 200)

    def test_delete_documents(self):
        delete_doc = documents[0]
        remain_doc = documents[1]
        self._delete_documents(delete_doc, remain_doc)

    def test_delete_no_doccode_documents(self):
        delete_doc = no_doccode_docs[0]
        remain_doc = no_doccode_docs[1]
        self._delete_documents(delete_doc, remain_doc)

        # Delete the other so we don't have to cleanup


    def test_get_rev_count(self):
        for f in documents:
            url = reverse('api_revision_count', kwargs = {'document': f})
            self.client.login(username=self.username, password=self.password)
            # do upload
            self._upload_file(f)
            response = self.client.get(url)
            if not response.content.isdigit():
                raise self.failureException('Invalid response: %s' % response.content)


    def test_get_bad_rev_count(self):
        url = reverse('api_revision_count', kwargs = {'document': 'sdfdsds42333333333333333333333333432423'})
        response = self.client.get(url)
        self.assertContains(response, 'Bad Request', status_code = 400)


    def test_z_cleanup(self):
        # Name of this test should be alphabetically last
        # to be ran after all tests finished

        # files cleanup using API
        url = reverse("api_file")
        self.client.login(username=self.username, password=self.password)

        # building proper cleanup list for normal docs
        cleanup_docs_list = []
        for doc in documents, [adl_invoice_name]:
            cleanup_docs_list.append(doc)

        # cleaning up simple docs
        for list in cleanup_docs_list:
            for doc in list:
                data = { 'filename': doc, }
                response = self.client.delete(url, data)
                self.assertEqual(response.status_code, 204)

        # cleaning up no doccode docs
        for doc in no_doccode_docs:
            data = { 'filename': doc + '.pdf' }
            response = self.client.delete(url, data)
            print "data %s" % data
            self.assertEqual(response.status_code, 204)

        # building proper list for docs that contain HASH
        for doc, hash in self.documents_hash:
            data = { 'filename': doc, }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)

        # unlisted docs cleanup
        for doc in unlisted_files_used:
            data = { 'filename': doc, }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)


