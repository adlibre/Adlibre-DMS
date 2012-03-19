import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth.models import User


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
        self.documents_norule = ('ABC12345678',)

        self.documents_hash = [
            ('abcde111', 'cad121990e04dcd5631a9239b3467ee9'),
            ('abcde123', 'bc3c5035805bb8098e5c164c5e1826da'),
            ('abcde222', 'ba7e656a1288181cdcf676c0d719939e'),
        ]

        self.documents_missing_hash = [
            ('abcde888','e9c84a6bcdefb9d01e7c0f9eabba5581',),
            ('abcde999','58a38de7b3652391f888f4e971c6e12e',),
        ]

        # These are documents that are not tested, yet exist in ./fixtures/testdata/
        self.unlisted_files_used = [
            'test_document_template.odt',
            'test_no_doccode.pdf',
            'ADL-12345.pdf',
            'ADL-54321.pdf',
            ]

        self.rules = (1, 2, 3, 4, 5,)
        self.rules_missing = (99,)

    def loadTestDocuments(self):
        # Load a copy of all our fixtures using the management command
        return call_command('import_documents', self.test_document_files_dir, silent=False)


    def setUp(self):
        # NB This is called once for every test, not just test case before the tests are run!

        # Create pr reset our test user (should be ok, even if fixtures contains this user)
#        self.user = User.objects.get_or_create(username=self.username)
#        self.user.set_password(self.password)
#        self.user.save()

        pass


    def tearDown(self):
        # Cleanup
        # TODO: Standardize the cleanup so no documents are left behind. Throw a warning if we find documents.
        pass


