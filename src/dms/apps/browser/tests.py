"""
Module: DMS Browser Django Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import magic

from django.conf import settings
from django.core.urlresolvers import reverse

from base_test import AdlibreTestCase

"""
Test data
"""
# auth user
username = 'admin'
password = 'admin'

documents_pdf = ('ADL-0001', 'ADL-0002', 'ADL-1111', 'ADL-1234', 'ADL-2222',)
documents_txt = ('10001', '10006', '101',)
documents_tif = ('2011-01-27-1', '2011-01-28-12',)
documents_missing = ('ADL-8888', 'ADL-9999',)
documents_norule = ('ABC12345678',)

unlisted_files_used = [
    'test_document_template.odt',
    'test_no_doccode.pdf',
    'ADL-12345.pdf',
    'ADL-54321.pdf',
]

documents_hash = [
    ('abcde111', 'cad121990e04dcd5631a9239b3467ee9'),
    ('abcde123', 'bc3c5035805bb8098e5c164c5e1826da'),
    ('abcde222', 'ba7e656a1288181cdcf676c0d719939e'),
    ]

documents_missing_hash = [
    ('abcde888','e9c84a6bcdefb9d01e7c0f9eabba5581',),
    ('abcde999','58a38de7b3652391f888f4e971c6e12e',),
    ]


rules = (1, 2, 3, 4,)
rules_missing = (99,)


class ViewTest(AdlibreTestCase):
    # TODO: Add test to upload files with no doccode.
    # TODO: Add test to upload files with wrong mime type.
    def _upload_file(self, filename):
        url = reverse("upload")
        self.client.login(username=username, password=password)
        # do upload
        data = { 'file': open(filename, 'r'), }
        response = self.client.post(url, data)
        return response

    def test_z_cleaup(self):
         # Name of this test should be alphabetically last
         # to be ran after all tests finished

         # files cleanup using API
         url = reverse("api_file")
         self.client.login(username=username, password=password)
         # building proper cleanup list for normal docs
         cleanup_docs_list = []
         for doc in documents_pdf, documents_tif, documents_txt:
             cleanup_docs_list.append(doc)
         # cleaning up simple docs
         for list in cleanup_docs_list:
             for doc in list:
                 data = { 'filename': doc, }
                 response = self.client.delete(url, data)
                 self.assertEqual(response.status_code, 204)

         # building proper list for docs that contain HASH
         cleanup_docs_list = []
         for doc in documents_hash, documents_missing_hash:
             cleanup_docs_list.append(doc)
         for list in cleanup_docs_list:
             for doc, hash in list:
                 data = { 'filename': doc, }
                 response = self.client.delete(url, data)
                 self.assertEqual(response.status_code, 204)

         # unlisted docs cleanup
         for doc in unlisted_files_used:
             data = { 'filename': doc, }
             response = self.client.delete(url, data)
             self.assertEqual(response.status_code, 204)

         # MAC specific cleanup:
         try:
             data = { 'filename': '.DS_Store' }
             response = self.client.delete(url, data)
         except:
             pass

    def test_upload_files(self):
        for doc_set, ext in [(documents_pdf, 'pdf'), (documents_txt, 'txt'), (documents_tif, 'tif') ]:
            for f in doc_set:
                response = self._upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.' + ext)
                self.assertContains(response, 'File has been uploaded')

    def test_upload_files_hash(self):
        for f in documents_hash:
            response = self._upload_file(settings.FIXTURE_DIRS[0] + '/testdata/' + f[0] + '.pdf')
            self.assertContains(response, 'File has been uploaded')

    # TODO: expand this to get documents with specific revisions.
    # FIXME: Currently failing on a fresh dataset. probably due to race condition.
    # TODO: Test document conversion, tiff2pdf, tiff2text
    def test_get_document(self):
        for d in documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, "You're not in security group", status_code = 403)
        self.client.login(username=username, password=password)
        
        mime = magic.Magic( mime = True )
        for d in documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            mimetype = mime.from_buffer( response.content )
            self.assertEquals(mimetype, 'application/pdf')
        for d in documents_pdf:
            url = '/get/' + d + '?extension=pdf'
            response = self.client.get(url)
            mimetype = mime.from_buffer( response.content )
            self.assertEquals(mimetype, 'application/pdf')
        for d in documents_missing:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, 'No such document', status_code = 404)


    def test_get_document_hash(self):
        self.client.login(username=username, password=password)
        for d in documents_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, '', status_code = 200)
        
        for d in documents_hash:
            url = '/get/%s.pdf?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, '', status_code = 200)

        for d in documents_hash:
            url = '/get/%s.pdf?hashcode=%s&extension=txt' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, '', status_code = 200)

        
        # TODO: fix this it will break...
        for d in documents_missing_hash:
            url = '/get/%s?hashcode=%s' % (d[0], d[1])
            response = self.client.get(url)
            self.assertContains(response, 'Hashcode did not validate', status_code = 500)
        

    def test_versions_view(self):
        self.client.login(username=username, password=password)
        for d in documents_pdf:
            url = '/revision/' + d
            response = self.client.get(url)
            self.assertContains(response, 'Revision of')

    def test_documents_view(self):
        self.client.login(username=username, password=password)
        for r in rules:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, 'Documents for')
        for r in rules_missing:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=404)

class SettingsTest(AdlibreTestCase):

    def test_settings_view(self):
        url = '/settings/'
        # un-authenticated request
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')
        self.assertContains(response, 'Log in |')
        # authenticated
        self.client.login(username=username, password=password)
        response = self.client.get(url)
        self.assertContains(response, 'Settings')

    def test_plugins_view(self):
        url = '/settings/plugins'
        # un-authenticated request
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')
        self.assertContains(response, 'Log in |')
        # authenticated
        self.client.login(username=username, password=password)
        response = self.client.get(url)
        self.assertContains(response, 'Plugins')


class MiscTest(AdlibreTestCase):

    def test_index_view(self):
        url = '/'
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre DMS')

    def test_documentation_view(self):
        url = '/docs/'
        response = self.client.get(url)
        self.assertContains(response, 'Documentation')


class ConversionTest(AdlibreTestCase):

    def test_tif2pdf_conversion(self):
        self.client.login(username=username, password=password)
        for d in documents_tif:
            url = '/get/' + d + '?extension=pdf'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_txt2pdf_conversion(self):
        self.client.login(username=username, password=password)
        for d in documents_txt:
            url = '/get/' + d + '?extension=pdf'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_pdf2txt_conversion(self):
        self.client.login(username=username, password=password)
        for d in documents_pdf:
            url = '/get/' + d + '?extension=txt'
            response = self.client.get(url)
            self.assertContains(response, d, status_code=200)
