"""
Module: DMS UI App Django Unit Tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

import os

from django.core.urlresolvers import reverse
from adlibre.dms.base_test import DMSTestCase


class MainDmsUiTest(DMSTestCase):
    """Main test for UI app"""

    def setUp(self):
        """ This is run before EVERY test"""
        # Create Logged in Client. We-re using only a logged in client in this tests
        self.client.login(username=self.username, password=self.password)
        self.upload_form_html = 'id="ui_upload_file_form" enctype="multipart/form-data" action="/ui/upload-document/"'
        self.regular_documents = [
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

    def _ui_upload(self, filename):
        # upload helper
        url = reverse('ui_upload_document')
        data = {'file': open(os.path.join(self.test_document_files_dir, filename), 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_through_ui(self):
        """ Test upload of test documents, covering all Regular Document Type Rules"""
        for filename in self.regular_documents:
            response = self._ui_upload(filename)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.upload_form_html)

    def test_zz_cleanup(self):
        """Test delete of test documents, covering all Regular Document Type Rules"""
        # Name of this test should be alphabetically last
        # to be ran after all tests finished
        for doc in self.regular_documents:
            code, suggested_format = os.path.splitext(doc)
            url = reverse('api_file', kwargs={'code': code, })
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)
