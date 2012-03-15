"""
Module: MDTUI tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import json, os, urllib, datetime
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
import re

# auth user
username = 'admin'
password = 'admin'

couchdb_url = 'http://127.0.0.1:5984'

test_mdt_docrule_id = 2 # should be properly assigned to fixtures docrule that uses CouchDB plugins

indexes_form_match_pattern = '(Employee ID|Employee Name|Friends ID|Friends Name).+?name=\"(\d+)\"'

mdt1 = {
    "docrule_id": str(test_mdt_docrule_id),
    "description": "Tests MDT number 1",
    "fields": {
       "1": {
           "type": "integer",
           "field_name": "Friends ID",
           "description": "ID of Friend for tests"
       },
       "2": {
           "type": "string",
           "length": 60,
           "field_name": "Friends Name",
           "description": "Name of tests person"
       },
    },
    "parallel": {
       "1": [ "1", "2"],
    }
}

mdt2 = {
    "docrule_id": str(test_mdt_docrule_id),
    "description": "Tests MDT number 2",
    "fields": {
       "1": {
           "type": "integer",
           "field_name": "Employee ID",
           "description": "Unique (Staff) ID of the person associated with the document"
       },
       "2": {
           "type": "string",
           "length": 60,
           "field_name": "Employee Name",
           "description": "Name of the person associated with the document"
       },
    },
    "parallel": {
       "1": [ "1", "2"],
    }
}

# Static dictionary of document to be indexed.
doc1_dict = {
    'date': '2012-03-06',
    'description': 'Test Document Number 1',
    'Employee ID': '123456',
    'Employee Name': 'Iurii Garmash',
    'Friends ID': '123',
    'Friends Name': 'Andrew',
}

doc1 = 'ADL-1111'


# TODO: Expand this (espetially search). Need to add at least 1 more docs...
class MDTUI(TestCase):
    def setUp(self):
        # We-re using only logged in client in this test
        self.client.login(username=username, password=password)

    def test_00_setup_initial(self):
        """
        Setup for those test suite. Made like standalone test because we need it to be run only once
        """
        # adding our MDT's required through API. (MDT API should be working)
        mdt = json.dumps(mdt1)
        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": mdt})
        self.assertEqual(response.status_code, 200)
        mdt = json.dumps(mdt2)
        response = self.client.post(url, {"mdt": mdt})
        self.assertEqual(response.status_code, 200)

    def test_01_opens_app(self):
        """
        If MDTUI app opens normally at least
        """
        url = reverse('mdtui-home')
        response = self.client.get(url)
        self.assertContains(response, 'To continue, choose from the options below')
        self.assertEqual(response.status_code, 200)

    def test_02_step1(self):
        """
        MDTUI Indexing has step 1 rendered properly.
        """
        url = reverse('mdtui-index')
        response = self.client.get(url)
        self.assertContains(response, '<legend>Step 1: Select Document Type</legend>')
        self.assertContains(response, 'Adlibre Invoices')
        self.assertEqual(response.status_code, 200)
    
    def test_03_step1_post_redirect(self):
        """
        MDTUI Displays Step 2 Properly (after proper call)
        """
        url = reverse('mdtui-index-1')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label class="control-label">Description</label>')
        self.assertContains(response, 'Creation Date')

    def test_04_indexing_step2_proper_form_rendering(self):
        """
        MDTUI renders Indexing form according to MDT's exist for testsuite's Docrule
        Step 2. Indexing Form contains MDT fields required.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-1')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Checking Step 2 Form
        url = reverse("mdtui-index-2")
        response = self.client.get(url)
        # contains Date field
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label class="control-label">Description</label>')
        self.assertContains(response, 'Creation Date')
        # Description field
        self.assertContains(response, 'id_description')
        # MDT based Fields:
        self.assertContains(response, "Friends ID")
        self.assertContains(response, "ID of Friend for tests")
        self.assertContains(response, "Friends Name")
        self.assertContains(response, "Name of tests person")
        self.assertContains(response, "Employee ID")
        self.assertContains(response, "Unique (Staff) ID of the person associated with the document")
        self.assertContains(response, "Employee Name")
        self.assertContains(response, "Name of the person associated with the document")
        #print response

    def test_05_adding_indexes(self):
        """
        MDTUI Indexing Form parses data properly.
        Step 3 Displays appropriate indexes fro document will be uploaded.
        Posting to Indexing Step 3 returns proper data.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-1')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-index-2")
        # Getting indexes form and matching form Indexing Form fields names
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc1_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response contains proper document indexes
        self.assertContains(response, 'Friends ID: 123')
        self.assertContains(response, 'Friends Name: Andrew')
        self.assertContains(response, 'Description: Test Document Number 1')
        self.assertContains(response, 'Creation Date: 2012-03-06')
        self.assertContains(response, 'Employee ID: 123456')
        self.assertContains(response, 'Employee Name: Iurii Garmash')
        # Contains Upload form
        self.assertContains(response, 'Upload File')
        self.assertContains(response, 'id_file')
        self.assertEqual(response.status_code, 200)

    def test_06_rendering_form_without_first_step(self):
        """
        Indexing Page 3 without populating previous forms contains proper warnings.
        """
        url = reverse("mdtui-index-3")
        response = self.client.get(url)
        self.assertContains(response, "You have not entered Document Indexing Data.")

    def test_07_posting_document_with_all_keys(self):
        """
        Uploading File though MDTUI, adding all Secondary indexes accordingly.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-1')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-2')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc1_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-3')
        response = self.client.get(url)
        self.assertContains(response, 'Friends ID: 123')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', doc1+'.pdf')
        data = { 'file': open(file, 'r'), 'filename':doc1}
        response = self.client.post(url, data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, 'Your document have just been indexed successfully!')
        self.assertContains(response, 'Friends Name: Andrew')
        self.assertContains(response, 'Start Again')

    def test_08_metadata_exists_for_uploaded_documents(self):
        """
        Document now exists in couchDB
        Querying CouchDB itself to test docs exist.
        """
        url = couchdb_url + '/dmscouch/'+doc1+'?revs_info=true'
        # HACK: faking 'request' object here
        r = self.client.get(url)
        cou = urllib.urlopen(url)
        resp = cou.read()
        r.status_code = 200
        r.content = resp
        self.assertContains(r, 'ADL-1111')
        self.assertContains(r, 'Iurii Garmash')

    def test_09_search_works(self):
        """
        Testing Search part opens.
        """
        url = reverse('mdtui-search')
        response = self.client.get(url)
        self.assertContains(response, 'Adlibre Invoices')
        self.assertContains(response, 'Document Search')
        self.assertEqual(response.status_code, 200)

    def test_10_search_indexes_warning(self):
        """
        Testing Search part Warning for indexes.
        """
        url = reverse('mdtui-search-options')
        response = self.client.get(url)
        self.assertContains(response, 'You have not defined Document Type Rule')
        self.assertEqual(response.status_code, 200)

    def test_11_search_results_warning(self):
        """
        Testing Search part  warning for results.
        """
        url = reverse('mdtui-search-results')
        response = self.client.get(url)
        self.assertContains(response, 'You have not defined Document Searching Options')
        self.assertEqual(response.status_code, 200)

    def test_12_search_docrule_select_improper_call(self):
        """
        Makes wrong request to view. Response returns back to docrule selection.
        """
        url = reverse('mdtui-search-type')
        response = self.client.post(url)
        self.assertContains(response, 'Adlibre Invoices')
        self.assertEqual(response.status_code, 200)

    def test_13_search_docrule_selection(self):
        """
        Proper Indexing call.
        """
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # checking for proper fields rendering
        self.assertContains(response, "Creation Date")
        self.assertContains(response, "Employee ID")
        self.assertContains(response, "Employee Name")
        self.assertContains(response, "Friends ID")
        self.assertContains(response, "Friends Name")
        self.assertNotContains(response, "Description</label>")
        self.assertNotContains(response, "You have not selected Doccument Type Rule")
        self.assertEqual(response.status_code, 200)

    def test_14_search_by_date_proper(self):
        """
        Proper call to search by date.
        MDTUI Search By Index Form parses data properly.
        Search Step 3 displays proper captured indexes.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1 Indexes
        response = self.client.post(url, {'date': doc1_dict["date"], '0':'', '1':'', '2':'', '3':''})
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # no errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # document found
        self.assertContains(response, doc1)
        self.assertContains(response, doc1_dict['description'])
        # context processors provide docrule name
        self.assertContains(response, "Adlibre Invoices")

    def test_15_search_by_key_proper(self):
        """
        Proper call to search by secondary index key.
        Search Step 3 displays proper captured indexes.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # assigning form fields
        url = reverse('mdtui-search-options')
        response = self.client.get(url)
        # Getting indexes form and matching form Indexing Form fields names
        rows_dict = self._read_indexes_form(response)
        search_dict = doc1_dict
        # Searching without date
        search_dict["date"] = ''
        post_dict = self._convert_doc_to_post_dict(rows_dict, search_dict)
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # no errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # document found
        self.assertContains(response, doc1)
        self.assertContains(response, doc1_dict['description'])
        # context processors provide docrule name
        self.assertContains(response, "Adlibre Invoices")

    def test_16_search_by_date_improper(self):
        """
        Imroper call to search by date.
        Search Step 3 does not display doc1.
        """
        # using today's date to avoid doc exists.
        date_req = datetime.datetime.now()
        date_str = datetime.datetime.strftime(date_req, "%Y-%m-%d")
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1 Indexes
        response = self.client.post(url, {'date': date_str, '0':'', '1':'', '2':'', '3':''})
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # no errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # document not found
        self.assertNotContains(response, doc1)

    def test_z_cleanup(self):
        """
        Cleaning up after all tests finished.
        Must be ran after all tests in this test suite.
        """
        #Deleting all- test MDT's (with doccode from var "test_mdt_docrule_id") using MDT's API.
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": str(test_mdt_docrule_id)})
        data = json.loads(str(response.content))
        for key, value in data.iteritems():
            mdt_id =  data[key]["mdt_id"]
            response = self.client.delete(url, {"mdt_id": mdt_id})
            self.assertEqual(response.status_code, 204)

        # Delete file "doc1"
        url = reverse("api_file")
        data = { 'filename': doc1, }
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, 204)

    def _read_indexes_form(self, response):
        """
        Helper to parse response with Document Indexing Form (MDTUI Indexing Step 2 Form)
        And returns key:value dict of form's dynamical fields for our tests.
        """
        prog = re.compile(indexes_form_match_pattern, re.DOTALL)
        matches_set = prog.findall(str(response))
        matches = {}
        for key,value in matches_set: matches[key]=value
        return matches

    def _convert_doc_to_post_dict(self, matches, doc):
        """
        Helper to convert Tests Documents into proper POST dictionary for Indexing Form testing.
        """
        post_doc_dict = {}
        for key, value in doc.iteritems():
            if key in matches.keys():
                post_doc_dict[matches[key]] = value
            else:
                post_doc_dict[key] = value
        return post_doc_dict

    def _retrieve_redirect_response_url(self, response):
        """
        helper parses 302 response object.
        Returns redirect url, parsed by regex.
        """
        self.assertEqual(response.status_code, 302)
        new_url = re.search("(?P<url>https?://[^\s]+)", str(response)).group("url")
        return new_url


