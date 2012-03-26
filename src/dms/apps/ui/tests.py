"""
Module: DMS UI Django Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

"""
Basic UI tests
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from adlibre.dms.base_test import DMSTestCase

import os


regular_documents = [
    '10001.txt',
    '10006.txt',
    '101.txt',
    '2011-01-27-1.tif',
    '2011-01-28-12.tif',
    'ADL-1111.pdf',
    'ADL-1234.pdf',
    'ADL-2222.pdf',
    'abcde111.pdf',
    'abcde123.pdf',
    'abcde222.pdf',
    'abcde888.pdf',
    'abcde999.pdf',
]

#nodoccode_documents = [
#    'ADL-12345.pdf',
#    'ADL-54321.pdf',
#    'test_document_template.odt',
#    'test_no_doccode.pdf',
#]

upload_form_html = """<form id="ui_upload_file_form" enctype="multipart/form-data" action="/ui/upload-document/" method="post">"""

class Main_DMS_UI_Test(DMSTestCase):

    def setUp(self):
        # NB This is run before EVERY test
        # Create Logged in Client. We-re using only a logged in client in this tests
        self.client.login(username=self.username, password=self.password)

    def _ui_upload(self, filename):
        # upload helper
        url = reverse('ui_upload_document')
        data = { 'file': open(os.path.join(self.test_document_files_dir, filename), 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_through_ui(self):
        # Test upload of test documents, covering all Regular Document Type Rules
        for filename in regular_documents:
            response = self._ui_upload(filename)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, upload_form_html)

#        # Test upload of test documents, covering all No Doc Code Type Rules
#        for filename in nodoccode_documents:
#            response = self._ui_upload(filename)
#            self.assertEqual(response.status_code, 200)
#            self.assertContains(response, upload_form_html)

    def test_zz_cleaup(self):
        # Name of this test should be alphabetically last
        # to be ran after all tests finished

        # Test delete of test documents, covering all Regular Document Type Rules
        for doc in regular_documents:
            code, suggested_format = os.path.splitext(doc)
            url = reverse('api_file', kwargs={'code': code,})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)

#        # Test delete of test documents, covering all No Doc Code Type Rules
#        for doc in nodoccode_documents:
#            code, suggested_format = os.path.splitext(doc)
#            url = reverse('api_file', kwargs={'code': code,})
#            from datetime import date # Hack
#            data = {'parent_directory': str(date.today()), 'full_filename': doc, } # hack
#            response = self.client.delete(url, data)
#            self.assertEqual(response.status_code, 204)