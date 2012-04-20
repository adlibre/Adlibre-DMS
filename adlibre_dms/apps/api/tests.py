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
# TODO: Run all of these tests for different auth. Plain, Django, and none!
# TODO: Test with and without correct permissions.

adlibre_invoices_rule_id = 1 # FIXME, we should have a dict of rules and ids provided by DMSTestCase

#no_doccode_name = "test_no_doccode"
adl_invoice_name = "ADL-1985"

# tagging
test_tag = 'test_tag'

class APITest(DMSTestCase):

    def test_00_setup(self):
        """
        Load Test Data
        """
        self.loadTestData()

    def test_api_rule_detail(self):
        self.client.login(username=self.username, password=self.password)
        doccode = DocumentTypeRuleManagerInstance.get_docrule_by_name('Test PDFs')
        mapping = DoccodePluginMapping.objects.get(doccode = doccode.get_id())
        #we don't really care if it crashes above, cause that means our database is imperfect
        url = reverse('api_rules_detail', kwargs={'id_rule': 2, 'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, 'Test PDFs')

    def test_api_rules(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_rules', kwargs={'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, 'Test PDFs')

    def test_api_plugins(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_plugins', kwargs={'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, 'dms_plugins.workers.storage.local.LocalStoragePlugin')

    def test_api_files(self):
        self.client.login(username=self.username, password=self.password)
        doccode = DocumentTypeRuleManagerInstance.get_docrule_by_name('Adlibre Invoices')
        mapping = DoccodePluginMapping.objects.get(doccode = doccode.get_id())
        url = reverse("api_file_list", kwargs = {'id_rule': mapping.pk})
        response = self.client.get(url)
        self.assertContains(response, 'ADL-1234')

    def test_api_file(self):
        self.client.login(username=self.username, password=self.password)
        doc = self.documents_hash[0][0]
        hash = self.documents_hash[0][1]
        # Upload first
        response = self._upload_file(doc)
        self.assertContains(response, '', status_code=200)
        # Download doc
        revision = 1
        url = reverse('api_file', kwargs={'code': doc, 'suggested_format': 'pdf',}) + '?r=%s&h=%s' % (revision, hash)
        response = self.client.get(url)
        self.assertContains(response, '', status_code=200)

    def test_api_fileinfo(self):
        self.client.login(username=self.username, password=self.password)
        for f in self.documents_pdf:
            url = reverse('api_file_info', kwargs={'code': f, })
            response = self.client.get(url)
            data = json.loads(response.content)
            if not 'document_name' in data or not (data['document_name'] == f):
                raise self.failureException('Invalid response: %s' % response.content)

#    def test_api_rename_no_doccode(self):
#        # Login
#        self.client.login(username=self.username, password=self.password)
#        # Upload no doccode
#        response = self._upload_file(no_doccode_name)
#        self.assertContains(response, '', status_code=200)
#        # Do rename
#        url = reverse('api_file', kwargs={'code': no_doccode_name, 'suggested_format': 'pdf',})
#        data = {'filename': no_doccode_name, 'new_name': adl_invoice_name,} #FIXME should be code, new_code
#        response = self.client.put(url, data)
#        self.assertContains(response, '', status_code=200)
#        # Fetch renamed file
#        url = reverse('api_file', kwargs={'code': adl_invoice_name, 'suggested_format': 'pdf',})
#        response = self.client.get(url)
#        # Fail to fetch old file
#        url = reverse('api_file', kwargs={'code': no_doccode_name, 'suggested_format': 'pdf',})
#        response = self.client.get(url)
#        self.assertContains(response, '', status_code=400)

    def test_api_tags(self):
        # Login
        self.client.login(username=self.username, password=self.password)
        # Upload file
        filename = self.documents_pdf[0]
        response = self._upload_file(filename)
        self.assertContains(response, '', status_code=200)
        # Remove tag
        url = reverse('api_file', kwargs={'code': filename,})
        data = {'filename': filename, 'remove_tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code=200)
        # Check that we don't have tag
        url = reverse('api_file_info', kwargs={'code': filename, })
        response = self.client.get(url)
        self.assertNotContains(response, test_tag, status_code=200)
        # Set tags
        url = reverse('api_file', kwargs={'code': filename,})
        data = {'filename': filename, 'tag_string': test_tag}
        response = self.client.put(url, data)
        self.assertContains(response, '', status_code=200)
        # Check that we have tag
        url = reverse('api_file_info', kwargs={'code': filename, })
        response = self.client.get(url)
        self.assertContains(response, test_tag, status_code=200)
        # Get all tags for rule, check our tag
        url = reverse('api_tags', kwargs={'id_rule': adlibre_invoices_rule_id, 'emitter_format': 'json'})
        response = self.client.get(url)
        self.assertContains(response, test_tag, status_code=200)

    def test_upload_files(self):
        for f in self.documents_pdf:
            response = self._upload_file(f)
            self.assertContains(response, f, status_code=200)

    def _delete_documents(self, delete_doc, remain_doc, suggested_format='pdf'):
        self.client.login(username=self.username, password=self.password)
        # Delete one
        url = reverse('api_file', kwargs={'code': delete_doc, 'suggested_format': suggested_format,})
        response = self.client.delete(url)
        self.assertContains(response, '', status_code=204)
        # Check the other still exists
        url = reverse('api_file', kwargs={'code': remain_doc, 'suggested_format': suggested_format,})
        response = self.client.get(url)
        self.assertContains(response, '', status_code=200)

    def test_delete_documents(self):
        delete_doc = self.documents_pdf[0]
        remain_doc = self.documents_pdf[1]
        self._delete_documents(delete_doc, remain_doc)

#    def test_delete_no_doccode_documents(self):
#        delete_doc = self.documents_norule[0]
#        remain_doc = self.documents_norule[1]
#        self._delete_documents(delete_doc, remain_doc)

    def test_get_rev_count(self):
        for f in self.documents_pdf:
            url = reverse('api_revision_count', kwargs={'document': f})
            self.client.login(username=self.username, password=self.password)
            # Do upload
            self._upload_file(f)
            response = self.client.get(url)
            if not response.content.isdigit():
                raise self.failureException('Invalid response: %s' % response.content)

    def test_get_bad_rev_count(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('api_revision_count', kwargs={'document': 'sdfdsds42333333333333333333333333432423'})
        response = self.client.get(url)
        self.assertContains(response, 'Bad Request', status_code=400)

    def test_zz_cleanup(self):
        """
        Test Cleanup
        """
        self.cleanAll(check_response=True)

        # Cleanup renamed doc adl_invoice_name (test currently disabled, so we don't need this)

