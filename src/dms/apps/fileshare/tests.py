from django.test import TestCase

from django.conf import settings


# TODO: Create a test document code, and a set of test documents at the start of test
"""
Test data
"""
# auth user
username = 'admin'
password = 'admin'

documents = ('ADL-1111', 'ADL-1234', 'ADL-2222',)
documents_missing = ()

rules = (1, 2,)
rules_missing = ()


class ViewTest(TestCase):

    # TODO: Add test to upload files with no doccode.
    # TODO: Add test to upload files with wrong mime type.
    def test_upload_files(self):
        for f in documents:
            url = '/upload/'
            self.client.login(username=username, password=password)

            file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.pdf'
            data = { 'file': open(file, 'r'), }
            response = self.client.post(url, data)
            self.assertContains(response, 'File has been uploaded')

    # TODO: expand this to get documents with specific revisions.
    # TODO: expand this to get documents that require a hash code.
    # FIXME: Currently failing on a fresh dataset. probably due to race condition.
    # TODO: Test with and without extension in request eg /get/ADL-1234.pdf
    # TODO: Test document conversion, tiff2pdf, tiff2text
    def test_get_document(self):
        for d in documents:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, '')
        # currently failing due to exception not 404 response
        for d in documents_missing:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, '', status_code=404)

    def test_versions_view(self):
        for d in documents:
            url = '/revision/' + d
            response = self.client.get(url)
            self.assertContains(response, 'Revision of')

    def test_documents_view(self):
        for r in rules:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, 'Documents for')
        # currently failing due to exception not 404 response
        for r in rules_missing:
            url = '/files/' + str(r) + '/'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=404)


class SettingsTest(TestCase):

    def test_settings_view(self):
        url = '/settings/'
        # un-authenticated request
        response = self.client.get(url)
        self.assertContains(response, 'Django administration')
        # authenticated
        self.client.login(username=username, password=password)
        response = self.client.get(url)
        self.assertContains(response, 'Settings')

    def test_plugins_view(self):
        url = '/settings/plugins'
        response = self.client.get(url)
        self.assertContains(response, 'Django administration')
        # authenticated
        self.client.login(username=username, password=password)
        response = self.client.get(url)
        self.assertContains(response, 'Plugins')


class MiscTest(TestCase):

    def test_index_view(self):
        url = '/'
        response = self.client.get(url)
        self.assertContains(response, 'The lightweight document management system')

    def test_documentation_view(self):
        url = '/docs/'
        response = self.client.get(url)
        self.assertContains(response, 'Documentation')
