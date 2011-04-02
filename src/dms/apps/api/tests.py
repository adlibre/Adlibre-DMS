"""
Module: API Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

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
# 1. Return revisions for a given file /api/revisions/ADL-1234.json
# 2. Return meta-data for a given file /api/metadata/ADL-1234.json
# 3. Delete files /api/delete/ADL-1234
# 4. Require authentication for API all actions.



# TODO: Write a test that checks these methods for ALL doctypes that are currently installed :)

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


    def test_upload_files(self):
        for f in documents:
            url = '/api/file/'
            self.client.login(username=username, password=password)
            # do upload
            file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.pdf'
            data = { 'file': open(file, 'r'), }
            response = self.client.post(url, data)
            self.assertContains(response, '', status_code=201)


    def test_delete_documents(self):
        for f in documents:
            url = '/api/file/?filename=' + f + '.pdf'
            # TODO: FIXME: Should require authentication
            #self.client.login(username=username, password=password)
            # do delete
            response = self.client.delete(url)
            self.assertContains(response, '', status_code=204)


    def test_get_rev_count(self):
        for f in documents:
            url = '/api/revision_count/' + f
            self.client.login(username=username, password=password)
            # do upload
            #file = settings.FIXTURE_DIRS[0] + '/testdata/' + f + '.pdf'
            #data = { 'filename': open(file, 'r'), }
            #response = self.client.post(url, data)
            response = self.client.get(url)
            self.assertContains(response, '')


    def test_get_bad_rev_count(self):
        url = '/api/revision_count/sdfdsds42333333333333333333333333432423'
        response = self.client.get(url)
        self.assertContains(response, 'Bad Request', status_code=400)

