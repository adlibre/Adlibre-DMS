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
from base_test import AdlibreTestCase

import os

# auth user
username = 'admin'
password = 'admin'

test_document_files_dir = settings.FIXTURE_DIRS[0] + '/testdata/'

test_document_files = [
    '10001.txt',
    '10006.txt',
    '101.txt',
    '2011-01-27-1.tif',
    '2011-01-28-12.tif',
    'ADL-1111.pdf',
    'ADL-1234.pdf',
    'ADL-12345.pdf',
    'ADL-2222.pdf',
    'ADL-54321.pdf',
    'abcde111.pdf',
    'abcde123.pdf',
    'abcde222.pdf',
    'abcde888.pdf',
    'abcde999.pdf',
    'test_document_template.odt',
    'test_no_doccode.pdf',
]

test_document_files_missing = ['ADL-8888.pdf', 'ADL-9999.pdf',]

upload_form_html = """<form id="ui_upload_file_form" enctype="multipart/form-data" action="/ui/upload-document/" method="post">"""

class Main_DMS_UI_Test(AdlibreTestCase):
    def setUp(self):
        # We-re using only logged in client in this test
        self.client.login(username=username, password=password)

    def _ui_upload(self, filename):
        # upload helper
        url = reverse('ui_upload_document')
        data = { 'file': open(os.path.join(test_document_files_dir, filename), 'r'), }
        response = self.client.post(url, data)
        return response

    def test_upload_through_ui(self):
        #testing upload by all Document Type Rule test files
        for filename in test_document_files:
            response = self._ui_upload(filename)
            self.assertNotEqual(response.status_code, 500)
            self.assertContains(response, upload_form_html)

    def test_z_cleaup(self):
        # Name of this test should be alphabetically last
        # to be ran after all tests finished

        # files cleanup using API
        url = reverse("api_file")

        for doc in test_document_files:
            data = { 'filename': doc, }
            response = self.client.delete(url, data)
            self.assertEqual(response.status_code, 204)

        # MAC specific cleanup:
        try:
         data = { 'filename': '.DS_Store' }
         response = self.client.delete(url, data)
        except:
         pass