import os
import base64

from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

__all__ = ['DMSTestCase', 'DMSBasicAuthenticatedTestCase',]

class DMSTestCase(TestCase):
    """
    Base Adlibre DMS Test Case

    Provides a standardized set of test data and ensures that each test run has a clean set of data.
    """
    fixtures = ['test_initial_data.json',]

    def __init__(self, *args, **kwargs):
        super(DMSTestCase, self).__init__(*args, **kwargs)

        # Test User Auth User
        self.username = 'admin'
        self.password = 'admin'

        # Source of documents
        self.test_document_files_dir = os.path.join(settings.FIXTURE_DIRS[0], 'testdata')

        # Test Data
        self.documents_pdf = ('ADL-0001', 'ADL-0002', 'ADL-1111', 'ADL-1234', 'ADL-2222',)
        self.documents_txt = ('10001', '10006', '101',)
        self.documents_tif = ('2011-01-27-1', '2011-01-28-12',)
        self.documents_missing = ('ADL-8888', 'ADL-9999',)
        self.documents_norule = ('ADL-54321', 'ADL-12345', ) # too long to match ADL invoices
        # These are documents that are not tested, yet exist in ./fixtures/testdata/
        self.unlisted_files_used = ('test_document_template.odt', 'test_no_doccode.pdf', )

        # Documents that exist, and have valid hash
        self.documents_hash = [
            ('abcde111', 'cad121990e04dcd5631a9239b3467ee9'),
            ('abcde123', 'bc3c5035805bb8098e5c164c5e1826da'),
            ('abcde222', 'ba7e656a1288181cdcf676c0d719939e'),
        ]

        # Documents that are missing, but have correct hash
        self.documents_missing_hash = [
            ('abcde888','e9c84a6bcdefb9d01e7c0f9eabba5581',),
            ('abcde999','58a38de7b3652391f888f4e971c6e12e',),
        ]

        # Documents with incorrect hashes
        self.documents_incorrect_hash = [
            # DEFINE ME
        ]

        self.rules = (1, 2, 3, 4, 5,)
        self.rules_missing = (99,)

    def loadTestDocuments(self):
        # Load a copy of all our fixtures using the management command
        return call_command('import_documents', self.test_document_files_dir, silent=False)

    def cleanUp(self, documents, check_response=True):
        """
        Cleanup Helper
        """
        self.client.login(username=self.username, password=self.password)
        for doc in documents:
            code, suggested_format = os.path.splitext(doc)
            url = reverse('api_file', kwargs={'code': code,})
            response = self.client.delete(url)
            if response.status_code is not 204:
                print "ERROR DATA: %s, %s" % (code, response.status_code)
            if check_response:
                self.assertEqual(response.status_code, 204)

    def cleanAll(self, check_response=True):
        """
        Clean all of our test documents
        """

        # Cleaning up simple docs
        self.cleanUp(self.documents_pdf, check_response=check_response)
        self.cleanUp(self.documents_tif, check_response=check_response)
        self.cleanUp(self.documents_txt, check_response=check_response)

        cleanup_docs_list = []
        # no doc code documents require full filename in order to delete FIXME!
        for doc in self.documents_norule:
            cleanup_docs_list.append('%s.pdf' % doc)
        self.cleanUp(cleanup_docs_list, check_response=check_response)

        # Cleanup hashed dicts
        # (I'm sure there is a more elegant way to do this)
        cleanup_docs_list = []
        for doc, hash in self.documents_hash:
            cleanup_docs_list.append(doc)
        for doc, hash in self.documents_missing_hash:
            cleanup_docs_list.append(doc)
        self.cleanUp(cleanup_docs_list, check_response=check_response)

        # Un used file cleanup
        self.cleanUp(self.unlisted_files_used, check_response=check_response)

    def setUp(self):
        # NB This is called once for every test, not just test case before the tests are run!
        pass

    def tearDown(self):
        # Cleanup
        # NB This is called once for every test, not just test case before the tests are run!
        pass


class BasicAuthClient(Client):
    """
    Basic HTTP Authentication Client
    user for testing Piston API
    """

    def auth(self, username, password):
        auth = '%s:%s' % (username, password)
        auth = 'Basic %s' % base64.encodestring(auth)
        auth = auth.strip()
        self.extra = {
            'HTTP_AUTHORIZATION': auth,
            }

    # Pass auth **extra to every method
    def get(self, *args, **kwargs):
        return super(BasicAuthClient, self).get(*args, **self.extra)

    def post(self, *args, **kwargs):
        return super(BasicAuthClient, self).post(*args, **self.extra)

    def head(self, *args, **kwargs):
        return super(BasicAuthClient, self).head(*args, **self.extra)

    def options(self, *args, **kwargs):
        return super(BasicAuthClient, self).options(*args, **self.extra)

    def put(self, *args, **kwargs):
        return super(BasicAuthClient, self).put(*args, **self.extra)

    def delete(self, *args, **kwargs):
        return super(BasicAuthClient, self).delete(*args, **self.extra)

class DMSBasicAuthenticatedTestCase(DMSTestCase):
    """
    Basic HTTP Authentication for our API Tests
    """

    client_class = BasicAuthClient

    def setUp(self, *args, **kwargs):
        super(DMSBasicAuthenticatedTestCase, self).setUp(*args, **kwargs)
        # Create Auth data
        self.client.auth(self.username, self.password)


