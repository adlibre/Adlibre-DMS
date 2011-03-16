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


# TODO: We need to extend the API to the following
# 1. Return revisions for a given file
# 2. Return meta-data for a given file
# 3. Delete files
# 4. Require authentication for API actions.



class MiscTest(TestCase):

    def test_api_rules(self):
        url = '/api/rules/1.json'
        response = self.client.get(url)
        self.assertContains(response, 'Local Storage')
        
        url = '/api/rules.json'
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre Invoices')


    def test_api_rules(self):
        url = '/api/plugins.json'
        response = self.client.get(url)
        self.assertContains(response, 'Security Group')

    def test_api_files(self):
        url = '/api/files/2/'
        response = self.client.get(url)
        self.assertContains(response, 'ADL-1234')
