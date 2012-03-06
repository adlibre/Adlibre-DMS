"""
Module: MDTUI tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import json, time
from django.test import TestCase
from django.core.urlresolvers import reverse
import re

# auth user
username = 'admin'
password = 'admin'

test_mdt_docrule_id = 2

indexes_form_match_pattern = '(Employee ID|Employee Name|Friends ID|Friends Name).+?name=\"(\d+)\"'

mdt1 = {
    "docrule_id": "2",
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
    "docrule_id": "2",
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



class MDTUI(TestCase):
    def setUp(self):
        # We-re using only logged in client in this test
        self.client.login(username=username, password=password)

    def _test_0_setup_initial(self):
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

    def test_1_opens_app(self):
        """
        If MDTUI app opens normally at least
        """
        url = reverse('mdtui-home')
        response = self.client.get(url)
        self.assertContains(response, 'To continue, choose from the options below')
        self.assertEqual(response.status_code, 200)

    def test_2_step1(self):
        """
        MDTUI Indexing has step 1 rendered properly.
        """
        url = reverse('mdtui-index')
        response = self.client.get(url)
        self.assertContains(response, '<legend>Step 1: Select Document Type</legend>')
        self.assertContains(response, 'Adlibre Invoices')
        self.assertEqual(response.status_code, 200)
    
    def test_3_step1_post_redirect(self):
        """
        MDTUI Displays Step 2 Properly (after proper call)
        """
        url = reverse('mdtui-index-1')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)

        #getting redirect url by regexp expression
        new_url = re.search("(?P<url>https?://[^\s]+)", str(response)).group("url")
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label class="control-label">Description</label>')
        self.assertContains(response, 'Creation Date')

#    def test_4_setp1_form_selected_when_returning(self):
#        print 4
#        """
#        MDTUI Indexing Docrule selection form preselected to
#        previous value when turning back from later steps.
#        """
#        url = reverse('mdtui-index')
#        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
#        self.assertEqual(response.status_code, 302)
#        url = reverse('mdtui-index')
#        response = self.client.get(url)
#        print response
#        #self.assertContains(response, '<option selected="selected" value="2">Adlibre Invoices</option>')
#        self.assertEqual(response.status_code, 200)

    def test_5_indexing_step2_proper_form_rendering(self):
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

    def test_5_adding_indexes(self):
        """
        MDTUI Indexing Form parses data properly.
        Step 3 Displays appropriate indexes fro document will be uploaded.
        POsting to Indexing Step 3 returns proper data.
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
        #getting redirect url by regexp expression
        new_url = re.search("(?P<url>https?://[^\s]+)", str(response)).group("url")
        response = self.client.get(new_url)
        # Response contains proper document indexes
        self.assertContains(response, 'Friends ID: 123')
        self.assertContains(response, 'Friends Name: Andrew')
        self.assertContains(response, 'Description: Test Document Number 1')
        self.assertContains(response, 'Creation Date: 2012-03-06')
        self.assertContains(response, 'Employee ID: 123456')
        self.assertContains(response, 'Employee Name: Iurii Garmash')
        self.assertEqual(response.status_code, 200)



    def test_6_rendering_form_without_first_step(self):
        """
        Indexing Page 3 without populating previous forms contains proper warnings.
        """
        url = reverse("mdtui-index-3")
        response = self.client.get(url)
        self.assertContains(response, "You have not entered Document Indexing Data.")

    def test_z_cleanup(self):
        """
        Cleaning up after all tests finished.
        Must be ran after all tests in this test suite.
        """
        # TODO: Proper cleanup after tests passed.
        pass

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