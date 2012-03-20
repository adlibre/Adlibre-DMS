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

"""
Test data
"""

# TODO: Create a test document code, and a set of test documents at the start of test
# TODO: Test self.rules, self.rules_missing, self.documents_missing
# TODO: Write a test that checks these methods for ALL doctypes that are currently installed :)

adlibre_invoices_rule_id = 1 # FIXME, we should have a dict of rules and ids provided by DMSTestCase

no_doccode_name = "test_no_doccode"
adl_invoice_name = "ADL-1985"

# tagging
test_tag = 'test_tag'

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
        for f in self.documents_pdf:
            url = reverse('api_file_info') + '?filename=%s' % f
            response = self.client.get(url)
            data = json.loads(response.content)
            if not 'document_name' in data or not (data['document_name'] == f):
                raise self.failureException('Invalid response: %s' % response.content)

    def test_api_rename_no_doccode(self):
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
        # Login
        self.client.login(username=self.username, password=self.password)
        # Upload file
        filename = self.documents_pdf[0]
        response = self._upload_file(filename)
        self.assertContains(response, '', status_code = 200)
        # Remove tag
        url = reverse('api_file') + '?filename=%s' % filename
        data = {'filename': filename, 'remove_tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        # Check that we don't have tag
        url = reverse('api_file_info')
        data = {'filename': filename}
        response = self.client.get(url, data)
        self.assertNotContains(response, test_tag, status_code = 200)
        # Set tags
        url = reverse('api_file') + '?filename=%s' % filename
        data = {'filename': filename, 'tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code = 200)
        # Check that we have tag
        url = reverse('api_file_info')
        data = {'filename': filename}
        response = self.client.get(url, data)
        self.assertContains(response, test_tag, status_code = 200)
        # Get all tags for rule, check our tag
        url = reverse('api_tags', kwargs = {'id_rule': adlibre_invoices_rule_id, 'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, test_tag, status_code = 200)

    def _upload_file(self, filename):
        url = reverse('api_file')
        self.client.login(username=self.username, password=self.password)
        # Do upload
        filepath = os.path.join(self.test_document_files_dir, filename + '.pdf')
        data = { 'file': open(filepath, 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_files(self):
        for f in self.documents_pdf:
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
        delete_doc = self.documents_pdf[0]
        remain_doc = self.documents_pdf[1]
        self._delete_documents(delete_doc, remain_doc)

    def test_delete_no_doccode_documents(self):
        delete_doc = self.documents_norule[0]
        remain_doc = self.documents_norule[1]
        self._delete_documents(delete_doc, remain_doc)

    def test_get_rev_count(self):
        for f in self.documents_pdf:
            url = reverse('api_revision_count', kwargs = {'document': f})
            self.client.login(username=self.username, password=self.password)
            # Do upload
            self._upload_file(f)
            response = self.client.get(url)
            if not response.content.isdigit():
                raise self.failureException('Invalid response: %s' % response.content)

    def test_get_bad_rev_count(self):
        url = reverse('api_revision_count', kwargs = {'document': 'sdfdsds42333333333333333333333333432423'})
        response = self.client.get(url)
        self.assertContains(response, 'Bad Request', status_code = 400)

    def test_z_cleanup(self):
        # Test should be alphabetically last
        # and run after all tests finished

        # files cleanup using API
        url = reverse("api_file")
        self.client.login(username=self.username, password=self.password)

        # building proper cleanup list for normal docs
        cleanup_docs_list = []
        for doc in self.documents_pdf, [adl_invoice_name]:
            cleanup_docs_list.append(doc)

        # cleaning up simple docs
        for list in cleanup_docs_list:
            for doc in list:
                data = { 'filename': doc, }
                response = self.client.delete(url, data)
                self.assertEqual(response.status_code, 204)

        # cleaning up no doccode docs
        for doc in (self.documents_norule[1],): # only one to cleanup
            data = { 'filename': doc + '.pdf' }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)

        # building proper list for docs that contain HASH
        # FIXME: These are deleted without a hash, we need to decide if hash is required for all methods for auth.
        for doc, hash in self.documents_hash:
            data = { 'filename': doc, }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)

        # unlisted docs cleanup
        for doc in (self.unlisted_files_used[0],): # only one to cleanup
            data = { 'filename': doc, }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)

        # cleaning up no documents_missing_hash docs
        for doc, hash in self.documents_missing_hash:
            data = { 'filename': doc }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)

