"""
Module: DMS Browser Django Unit Tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import magic

from django.conf import settings
from django.core.urlresolvers import reverse

from adlibre.dms.base_test import DMSTestCase

# Used in determining if current file is PDF file by 'string' inside a file content.
pdf_file_string_part = '%PDF-1.4'

class ViewTest(DMSTestCase):
    """
    Adlibre Browser Views and functionality test case

    Test data is provided by DMSTestCase
    """

    # TODO: Add test to upload files with no doccode.
    # TODO: Add test to upload files with wrong mime type.

    def test_00_setup(self):
        # Load Test Data
        self.loadTestData()

    def test_zz_cleanup(self):
        """
        Test Cleanup
        """
        self.cleanAll(check_response=True)


    def browser_upload_file(self, filename):
        url = reverse('upload')
        self.client.login(username=self.username, password=self.password)
        # Do upload
        data = { 'file': open(filename, 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_files(self):
        for doc_set, ext in [(self.documents_pdf, 'pdf'), (self.documents_txt, 'txt'), (self.documents_tif, 'tif') ]:
            for f in doc_set:
                response = self.browser_upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.' + ext)
                self.assertContains(response, 'File has been uploaded')

    def test_upload_files_hash(self):
        for f in self.documents_hash:
            response = self.browser_upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f[0] + '.pdf')
            self.assertContains(response, 'File has been uploaded')

    # TODO: expand this to get documents with specific revisions.
    def test_get_document(self):
        # Test security group required
        for d in self.documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, "You're not in security group", status_code=403)
        self.client.login(username=self.username, password=self.password)
        # Check mime type
        mime = magic.Magic( mime = True )
        for d in self.documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            mimetype = mime.from_buffer( response.content )
            self.assertEquals(mimetype, 'application/pdf')
        for d in self.documents_pdf:
            url = '/get/' + d + '?extension=pdf'
            response = self.client.get(url)
            mimetype = mime.from_buffer( response.content )
            self.assertEquals(mimetype, 'application/pdf')
        # Check 404 on missing documents
        for d in self.documents_missing:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, 'No such document', status_code=404)

    def test_get_document_hash(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, pdf_file_string_part, status_code=200)
        
        for d in self.documents_hash:
            url = '/get/%s.pdf?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, pdf_file_string_part, status_code=200)

        for d in self.documents_hash:
            url = '/get/%s.pdf?hashcode=%s&extension=txt' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, pdf_file_string_part, status_code=200)

        # TODO: fix this it will break...
        for d in self.documents_missing_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, 'Hashcode did not validate', status_code=500)

    def test_versions_view(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_pdf:
            url = '/revision/' + d
            response = self.client.get(url)
            self.assertContains(response, 'Revision of')

    def test_documents_view(self):
        self.client.login(username=self.username, password=self.password)
        for r in self.rules:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, 'Documents for')
        for r in self.rules_missing:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=404)

    def test_displays_all_required_documents(self):
        """
        Documents found by browser app and rendered properly by API.

        Backend provides all proper data for browser 'view documents list for docrule' section.
        """
        self.client.login(username=self.username, password=self.password)
        for rule_id in ['2', '7']:
            url = reverse('files_document', kwargs={'id_rule':rule_id})
            data = {"finish": "15",
                    "order": "created_date",
                    "start": "0"
                    }
            response = self.client.post(url, data)
            if rule_id == '2':
                self._check_docs_exist(
                    response,
                    self.documents_pdf,
                    [self.documents_missing, self.documents_tif, self.documents_txt]
                )
            if rule_id == '7':
                self._check_docs_exist(
                    response,
                    self.documents_pdf2,
                    [self.documents_pdf, self.documents_missing, self.documents_tif, self.documents_txt]
                )

    def _check_docs_exist(self, response, exist, not_exist_list_of_lists):
        """Helper to check for documents names present/absent in response"""
        for doc_name in exist:
            self.assertContains(response, doc_name)
        for not_exist_list in not_exist_list_of_lists:
            for doc_name in not_exist_list:
                self.assertNotContains(response, doc_name)

class SettingsTest(DMSTestCase):

    def test_settings_view(self):
        url = '/settings/'
        # un-authenticated request
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')
        self.assertContains(response, 'Log in |')
        # authenticated
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertContains(response, 'Settings')

    def test_plugins_view(self):
        url = '/settings/plugins'
        # un-authenticated request
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')
        self.assertContains(response, 'Log in |')
        # authenticated
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertContains(response, 'Plugins')


class MiscViewTest(DMSTestCase):

    def test_index_view(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')

    def test_documentation_view(self):
        url = reverse('documentation_index')
        response = self.client.get(url)
        self.assertContains(response, 'Documentation')


class ConversionTest(DMSTestCase):

    def test_00_setup(self):
        # Load Test Data
        self.loadTestData()

    def test_tif2pdf_conversion(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_tif:
            url = reverse('get_file', kwargs={'code': d, 'suggested_format': 'pdf',})
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_txt2pdf_conversion(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_txt:
            url = reverse('get_file', kwargs={'code': d, 'suggested_format': 'pdf',})
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_pdf2txt_conversion(self):
        self.client.login(username=self.username, password=self.password)
        # FIXME: real pdf to txt conversion not tested here. Do we really need it?
        for d in self.documents_pdf:
            url = reverse('get_file', kwargs={'code': d, 'suggested_format': 'txt',})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_zz_cleanup(self):
        """Test Cleanup"""
        self.cleanAll(check_response=True)
