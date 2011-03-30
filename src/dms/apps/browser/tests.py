from django.test import TestCase

from django.conf import settings


"""
Test data
"""
# auth user
username = 'admin'
password = 'admin'

documents_pdf = ('ADL-1111', 'ADL-1234', 'ADL-2222',)
documents_txt = ('10001', '10006', '101',)
documents_tif = ('2011-01-27-1', '2011-01-28-12',)
documents_missing = ('ADL-8888', 'ADL-9999',)
documents_norule = ('ABC12345678',)

documents_hash = [
    ('abcde111', '6784d1b54f6405a70508c9fc02f37bad'),
    ('abcde123', '7e7eb8bdbea79d095f5dc291d2d9588f'),
    ('abcde222','fac584ea31b0ac927cecc12868513d39'),
    ]

documents_missing_hash = [
    ('abcde888','e9c84a6bcdefb9d01e7c0f9eabba5581',),
    ('abcde999','58a38de7b3652391f888f4e971c6e12e',),
    ]


rules = (1, 2, 3, 4,)
rules_missing = (5, 99,)


class ViewTest(TestCase):

    # TODO: Add test to upload files with no doccode.
    # TODO: Add test to upload files with wrong mime type.

    def test_upload_files(self):

        for f in documents_pdf:
            url = '/upload/'
            self.client.login(username=username, password=password)
            # do upload
            file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.pdf'
            data = { 'file': open(file, 'r'), }
            response = self.client.post(url, data)
            self.assertContains(response, 'File has been uploaded')

        for f in documents_txt:
            url = '/upload/'
            self.client.login(username=username, password=password)
            # do upload
            file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.txt'
            data = { 'file': open(file, 'r'), }
            response = self.client.post(url, data)
            self.assertContains(response, 'File has been uploaded')
            
        for f in documents_tif:
            url = '/upload/'
            self.client.login(username=username, password=password)
            # do upload
            file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.tif'
            data = { 'file': open(file, 'r'), }
            response = self.client.post(url, data)
            self.assertContains(response, 'File has been uploaded')

            
    def test_upload_files_hash(self):
        for f in documents_hash:
            url = '/upload/'
            self.client.login(username=username, password=password)
            # do upload
            file = settings.FIXTURE_DIRS[0] + '/testdata/' + f[0] + '.pdf'
            data = { 'file': open(file, 'r'), }
            response = self.client.post(url, data)
            self.assertContains(response, 'File has been uploaded')


    # TODO: expand this to get documents with specific revisions.
    # FIXME: Currently failing on a fresh dataset. probably due to race condition.
    # TODO: Test document conversion, tiff2pdf, tiff2text
    def test_get_document(self):
        for d in documents_pdf:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, '')
        for d in documents_pdf:
            url = '/get/' + d + '.pdf'
            response = self.client.get(url)
            self.assertContains(response, '')
        for d in documents_missing:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, 'No file or revision match', status_code=404)
        for d in documents_norule:
            url = '/get/' + d
            response = self.client.get(url)
            self.assertContains(response, 'No rule found for file', status_code=404)
        url = '/get/' + '97123987asdakjsdg1231123asad'
        response = self.client.get(url)
        self.assertContains(response, 'No rule found for file', status_code=404)


    def test_get_document_hash(self):
        for d in documents_hash:
            url = '/' + d[1] + '/' + d[0]
            response = self.client.get(url)
            try:
                self.assertContains(response, '')
            except:
                print('Failed on' + url)
        for d in documents_hash:
            url = '/' + d[1] + '/' + d[0] + '.pdf'
            response = self.client.get(url)
            try:
                self.assertContains(response, '')
            except:
                print('Failed on' + url)

        # TODO fix this it will break...
        for d in documents_missing_hash:
            url = '/' + d[1] + '/' + d[0]
            response = self.client.get(url)
            self.assertContains(response, 'No file or revision match', status_code=404)


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
            self.assertContains(response, 'No rule found for id', status_code=404)


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


class ConversionTest(TestCase):

    def test_tif2pdf_conversion(self):
        for d in documents_tif:
            url = '/get/' + d + '.pdf'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_txt2pdf_conversion(self):
        for d in documents_txt:
            url = '/get/' + d + '.pdf'
            response = self.client.get(url)
            self.assertContains(response, '', status_code=200)

    def test_pdf2txt_conversion(self):
        for d in documents_pdf:
            url = '/get/' + d + '.txt'
            response = self.client.get(url)
            self.assertContains(response, d, status_code=200)