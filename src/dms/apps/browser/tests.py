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


class ViewTest(DMSTestCase):
    """
    Adlibre Browser Views and functionality test case

    Test data is provided by DMSTestCase
    """

    def setUp(self):
        # Load Test Data
        self.loadTestDocuments()

        # TODO: Add test to upload files with no doccode.
    # TODO: Add test to upload files with wrong mime type.
    def _upload_file(self, filename):
        url = reverse("upload")
        self.client.login(username=self.username, password=self.password)
        # do upload
        data = { 'file': open(filename, 'r'), }
        response = self.client.post(url, data)
        return response

    def test_z_cleaup(self):
        """
        Test Cleanup
        """
        # Name of this test should be alphabetically last
        # to be ran after all tests finished

        # files cleanup using API
        url = reverse("api_file")
        self.client.login(username=self.username, password=self.password)
        # building proper cleanup list for normal docs
        cleanup_docs_list = []
        for doc in self.documents_pdf, self.documents_tif, self.documents_txt:
            cleanup_docs_list.append(doc)
        # cleaning up simple docs
        for list in cleanup_docs_list:
            for doc in list:
                data = { 'filename': doc, }
                response = self.client.delete(url, data)
                self.assertEqual(response.status_code, 204)

        # building proper list for docs that contain HASH
        cleanup_docs_list = []
        for doc in self.documents_hash, self.documents_missing_hash:
            cleanup_docs_list.append(doc)
        for list in cleanup_docs_list:
            for doc, hash in list:
                data = { 'filename': doc, }
                response = self.client.delete(url, data)
                self.assertEqual(response.status_code, 204)

        # unlisted docs cleanup
        for doc in self.unlisted_files_used:
            data = { 'filename': doc, }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)

    def test_upload_files(self):
        for doc_set, ext in [(self.documents_pdf, 'pdf'), (self.documents_txt, 'txt'), (self.documents_tif, 'tif') ]:
            for f in doc_set:
                response = self._upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.' + ext)
                self.assertContains(response, 'File has been uploaded')

    def test_upload_files_hash(self):
        for f in self.documents_hash:
            response = self._upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f[0] + '.pdf')
            self.assertContains(response, 'File has been uploaded')

    # TODO: expand this to get documents with specific revisions.
    # FIXME: Currently failing on a fresh dataset. probably due to race condition.
    # TODO: Test document conversion, tiff2pdf, tiff2text
    def test_get_document(self):
        for d in self.documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, "You're not in security group", status_code = 403)
        self.client.login(username=self.username, password=self.password)
        
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
        for d in self.documents_missing:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, 'No such document', status_code = 404)


    def test_get_document_hash(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, '', status_code = 200)
        
        for d in self.documents_hash:
            url = '/get/%s.pdf?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, '', status_code = 200)

        for d in self.documents_hash:
            url = '/get/%s.pdf?hashcode=%s&extension=txt' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, '', status_code = 200)

        # TODO: fix this it will break...
        for d in self.documents_missing_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, 'Hashcode did not validate', status_code = 500)
        

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

    def setUp(self):
        # Load Test Data
        self.loadTestDocuments()

    def test_tif2pdf_conversion(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_tif:
            url = '/get/' + d + '?extension=pdf'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_txt2pdf_conversion(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_txt:
            url = '/get/' + d + '?extension=pdf'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_pdf2txt_conversion(self):
        self.client.login(username=self.username, password=self.password)
        for d in self.documents_pdf:
            url = '/get/' + d + '?extension=txt'
            response = self.client.get(url)
            self.assertContains(response, d, status_code=200)
