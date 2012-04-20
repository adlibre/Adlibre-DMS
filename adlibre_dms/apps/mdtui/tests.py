"""
Module: MDTUI tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import json, os, urllib, datetime
from couchdbkit import Server
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
import re

# auth user
username = 'admin'
password = 'admin'

couchdb_url = 'http://127.0.0.1:5984'

test_mdt_docrule_id = 2 # should be properly assigned to fixtures docrule that uses CouchDB plugins
test_mdt_docrule_id2 = 6 # should be properly assigned to fixtures docrule that uses CouchDB plugins
test_mdt_docrule_id3 = 7 # should be properly assigned to fixtures docrule that uses CouchDB plugins

indexes_form_match_pattern = '(Employee ID|Employee Name|Friends ID|Friends Name|Required Date|Reporting Entity|Report Date|Report Type).+?name=\"(\d+)\"'

mdt1 = {
    "_id": 'mdt1',
    "docrule_id": [str(test_mdt_docrule_id),],
    "description": "Test MDT Number 1",
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
       "3": {
           "type": "date",
           "field_name": "Required Date",
           "description": "Testing Date Type Secondary Key"
       },
    },
    "parallel": {
       "1": [ "1", "2"],
    }
}

mdt2 = {
    "_id": 'mdt2',
    "docrule_id": [str(test_mdt_docrule_id),],
    "description": "Test MDT Number 2",
    "fields": {
       "1": {
           "type": "integer",
           "field_name": "Employee ID",
           "description": "Unique (Staff) ID of the person associated with the document"
       },
       "2": {
           "type": "string",
           "field_name": "Employee Name",
           "description": "Name of the person associated with the document"
       },
    },
    "parallel": {
       "1": [ "1", "2"],
    }
}

mdt3 = {
    "_id": 'mdt3',
    "docrule_id": [str(test_mdt_docrule_id2),],
    "description": "Test MDT Number 3",
    "fields": {
        "1": {
            "type": "string",
            "length": 3,
            "field_name": "Reporting Entity",
            "description": "(e.g. JTG, QH, etc)"
        },
        "2": {
            "type": "string",
            "length": 60,
            "field_name": "Report Type",
            "description": "Report Type (e.g. Reconciliation, Pay run etc)"
        },
        "3": {
            "type": "date",
            "field_name": "Report Date",
            "description": "Date the report was generated"
        },
    },
    "parallel": {}
}

mdt4 = {
    "_id": 'mdt4',
    "docrule_id": [str(test_mdt_docrule_id3),],
    "description": "Test MDT Number 4",
    "fields": {
            "1": {
                "type": "string",
                "uppercase": "yes",
                "field_name": "Tests Uppercase Field",
                "description": "This field's value must be converted uppercase even if entered lowercase"
            }
        },
    "parallel": {}
}

# Static dictionary of documents to be indexed for mdt1 and mdt2
doc1_dict = {
    'date': '2012-03-06',
    'description': 'Test Document Number 1',
    'Employee ID': '123456',
    'Required Date': '2012-03-07',
    'Employee Name': 'Iurii Garmash',
    'Friends ID': '123',
    'Friends Name': 'Andrew',
}

doc2_dict = {
    'date': '2012-03-20',
    'description': 'Test Document Number 2',
    'Employee ID': '111111',
    'Required Date': '2012-03-21',
    'Employee Name': 'Andrew Cutler',
    'Friends ID': '321',
    'Friends Name': 'Yuri',
}

doc3_dict = {
    'date': '2012-03-28',
    'description': 'Test Document Number 3',
    'Employee ID': '111111',
    'Required Date': '2012-03-29',
    'Employee Name': 'Andrew Cutler',
    'Friends ID': '222',
    'Friends Name': 'Someone',
}

# Static dictionary of documents to be indexed for mdt3
m2_doc1_dict = {
    'date': '2012-04-01',
    'description': 'Test Document MDT 3 Number 1',
    'Reporting Entity': 'JTG',
    'Report Date': '2012-04-01',
    'Report Type': 'Reconciliation',
}

m2_doc2_dict = {
    'date': '2012-04-03',
    'description': 'Test Document MDT 3 Number 2',
    'Reporting Entity': 'FCB',
    'Report Date': '2012-04-04',
    'Report Type': 'Pay run',
}

doc1 = 'ADL-0001'
doc2 = 'ADL-0002'
doc3 = 'ADL-1111'

# Proper for doc1
typehead_call1 = {
                'key_name': "Friends ID",
                "autocomplete_search": "1"
                }
typehead_call2 = {
                'key_name': "Employee ID",
                "autocomplete_search": "12"
                }

# Improper for doc1
typehead_call3 = {
                'key_name': "Employee ID",
                "autocomplete_search": "And"
                }

# Proper date range calls
all3_docs_range = {u'end_date':u'2012-03-30', u'1':u'', u'0':u'', u'3':u'', u'2':u'', u'4':u'', u'date':u'2012-03-01',}
all_docs_range = {u'end_date':u'2012-04-30', u'1':u'', u'0':u'', u'2':u'',u'date':u'2012-03-01',} # Search by docrule2 MDT3
date_range_1and2_not3 = {u'end_date':u'2012-03-20', u'1':u'', u'0':u'', u'3':u'', u'2':u'', u'4':u'', u'date':u'2012-03-01',}
date_range_only3 = {u'end_date':u'2012-03-30', u'1':u'', u'0':u'', u'3':u'', u'2':u'', u'4':u'', u'date':u'2012-03-25',}
date_range_none = {u'end_date':u'2012-03-31', u'1':u'', u'0':u'', u'3':u'', u'2':u'', u'4':u'', u'date':u'2012-03-30',}

# Proper date range with keys search
date_range_with_keys_3_docs = {u'date':u'2012-03-01', u'end_date':u'2012-03-30',} # Date range for 3 docs
date_range_with_keys_doc1 = {u'Employee ID': u'123456', u'Employee Name': u'Iurii Garmash',} # Unique keys for doc1
date_range_with_keys_doc2 = {u'Employee Name': u'Andrew Cutler',} # Unique keys for docs 2 and 3
date_type_key_doc1 = {u'Required Date': u'2012-03-07',} # Unique date type ley for doc 1

# Uppercase fields
upper_wrong_dict = {u'date': [u'2012-04-17'], u'0': [u'lowercase data'], u'description': [u'something usefull']}
upper_right_dict = {u'date': [u'2012-04-17'], u'0': [u'UPPERCASE DATA'], u'description': [u'something usefull']}

# TODO: test proper CSV export, even just simply, with date range and list of files present there

# TODO: test posting docs to 2 different document type rules and mix out parallel keys and normal search here for proper behaviour:
# THIS IS WRONG:
# 1. search does not filter on MDT correctly. Getting results from multiple MDTs (and document types).
# 2. parallel key lookups are not sharing parallel info across document types.

class MDTUI(TestCase):

    def setUp(self):
        # We are using only logged in client in this test
        self.client.login(username=username, password=password)

    def test_00_setup_mdt1(self):
        """
        Setup MDT 1 for the test suite. Made like standalone test because we need it to be run only once
        """
        # adding our MDT's required through API. (MDT API should be working)
        mdt = json.dumps(mdt1)
        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": mdt})
        self.assertEqual(response.status_code, 200)

    def test_00_setup_mdt2(self):
        """
        Setup MDT 2 for the test suite. Made like standalone test because we need it to be run only once
        """
        # adding our MDT's required through API. (MDT API should be working)
        mdt = json.dumps(mdt2)
        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": mdt})
        self.assertEqual(response.status_code, 200)

    def test_00_setup_mdt3(self):
        """
        Setup MDT 3 for the test suite. Made like standalone test because we need it to be run only once
        """
        # adding our MDT's required through API. (MDT API should be working)
        mdt = json.dumps(mdt3)
        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": mdt})
        self.assertEqual(response.status_code, 200)

    def test_00_setup_mdt4(self):
        """
        Setup MDT 4 for the test suite. Made like standalone test because we need it to be run only once
        """
        # adding our MDT's required through API. (MDT API should be working)
        mdt = json.dumps(mdt4)
        url = reverse('api_mdt')
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
        url = reverse('mdtui-index-type')
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
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Checking Step 2 Form
        url = reverse("mdtui-index-details")
        response = self.client.get(url)
        # contains Date field
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label class="control-label">Description</label>')
        self.assertContains(response, 'Creation Date')
        # Description field
        self.assertContains(response, 'id_description')
        # MDT based Fields:
        self.assertContains(response, "Friends ID")
        self.assertContains(response, "Required Date")
        self.assertContains(response, "ID of Friend for tests")
        self.assertContains(response, "Friends Name")
        self.assertContains(response, "Name of tests person")
        self.assertContains(response, "Employee ID")
        self.assertContains(response, "Unique (Staff) ID of the person associated with the document")
        self.assertContains(response, "Employee Name")
        self.assertContains(response, "Name of the person associated with the document")
        self.assertContains(response, "Required Date")
        self.assertContains(response, "Testing Date Type Secondary Key")

    def test_05_adding_indexes(self):
        """
        MDTUI Indexing Form parses data properly.
        Step 3 Displays appropriate indexes fro document will be uploaded.
        Posting to Indexing Step 3 returns proper data.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-index-details")
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
        self.assertContains(response, 'Required Date: 2012-03-07')
        # Contains Upload form
        self.assertContains(response, 'Upload File')
        self.assertContains(response, 'id_file')
        self.assertEqual(response.status_code, 200)

    def test_06_rendering_form_without_first_step(self):
        """
        Indexing Page 3 without populating previous forms contains proper warnings.
        """
        url = reverse("mdtui-index-source")
        response = self.client.get(url)
        self.assertContains(response, "You have not entered Document Indexing Data.")

    def test_07_posting_document_with_all_keys(self):
        """
        Uploading File though MDTUI, adding all Secondary indexes accordingly.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc1_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertContains(response, 'Friends ID: 123')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', doc1+'.pdf')
        data = { 'file': open(file, 'rb'), 'post_data':'to make request post type'}
        response = self.client.post(url, data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, 'Your document has been indexed successfully')
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
        self.assertContains(r, doc1)
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
        self.assertContains(response, 'You have not defined Document Type.')
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
        self.assertContains(response, "Creation Date From")
        self.assertContains(response, "To")
        self.assertContains(response, "Employee ID")
        self.assertContains(response, "Employee Name")
        self.assertContains(response, "Friends ID")
        self.assertContains(response, "Friends Name")
        self.assertContains(response, "Required Date")
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
        response = self.client.post(url, {'date': doc1_dict["date"], 'end_date': '', '0':'', '1':'', '2':'', '3':'', '4':''})
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
        search_dict = self._createa_search_dict(doc1_dict)
        # Search without a description (we can't yet search on this field)
        del search_dict['description']
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
        # context processors provide docrule name
        self.assertContains(response, "Adlibre Invoices")

    def test_16_search_by_date_improper(self):
        """
        Improper call to search by date.
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

    def test_17_add_indexes_unvalidated_form_preserves_prepopulated_data(self):
        """
        MDTUI Indexing Form .
        Step 2 adding indexes into several fields instead of all required
        returns prepopulated form with errors.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-index-details")
        # Getting indexes form and matching form Indexing Form fields names
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc1_dict)
        # Modifying post to brake it
        post_dict["description"]=u''
        post_dict["0"] = u''
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 200)
        # Response contains proper validation data
        self.assertContains(response, 'Brief Document Description') # form fields help exists
        self.assertContains(response, 'Name of tests person')
        self.assertContains(response, '2012-03-06') # docs data populated into form
        self.assertContains(response, 'Andrew')
        self.assertContains(response, '123456')
        self.assertContains(response, 'Iurii Garmash')
        self.assertContains(response, '// autocomplete for field Friends ID') # autocomplete (typehead) scripts rendered
        self.assertContains(response, '// autocomplete for field Friends Name')
        self.assertContains(response, 'This field is required') # form renders errors

    def test_18_parallel_keys_indexing_proper(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call1)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>') # json but not html response
        self.assertContains(response, 'Friends ID') # Proper keys
        self.assertContains(response, '123')
        self.assertContains(response, 'Friends Name')
        self.assertContains(response, 'Andrew')
        self.assertNotContains(response, 'Iurii Garmash') # Improper key
        self.assertNotContains(response, 'Employee Name')
        self.assertNotContains(response, 'Required Date')

    def test_19_parallel_keys_indexing_wrong(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call3)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>')
        self.assertNotContains(response, 'Friends ID')
        self.assertNotContains(response, '123')
        self.assertNotContains(response, 'Friends Name')
        self.assertNotContains(response, 'Andrew')
        self.assertNotContains(response, 'Iurii Garmash')
        self.assertNotContains(response, 'Employee Name')
        self.assertNotContains(response, 'Required Date')

    def test_20_parallel_keys_indexing_set2_proper(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call2)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>')
        self.assertNotContains(response, 'Friends ID')
        self.assertNotContains(response, 'Friends Name')
        self.assertNotContains(response, 'Andrew')
        self.assertNotContains(response, 'Required Date')
        self.assertContains(response, 'Iurii Garmash')
        self.assertContains(response, 'Employee Name')
        self.assertContains(response, 'Employee ID')
        self.assertContains(response, '123456')

    def test_21_parallel_keys_search_proper(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-search-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        # Adding Document Indexes
        response = self.client.post(url, typehead_call1)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>') # json but not html response
        self.assertContains(response, 'Friends ID') # Proper keys
        self.assertContains(response, '123')
        self.assertContains(response, 'Friends Name')
        self.assertContains(response, 'Andrew')
        self.assertNotContains(response, 'Iurii Garmash') # Improper key
        self.assertNotContains(response, 'Employee Name')

    def test_22_parallel_keys_searching_set2_proper(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-search-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call2)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>')
        self.assertNotContains(response, 'Friends ID')
        self.assertNotContains(response, 'Friends Name')
        self.assertNotContains(response, 'Andrew')
        self.assertContains(response, 'Iurii Garmash')
        self.assertContains(response, 'Employee Name')
        self.assertContains(response, 'Employee ID')
        self.assertContains(response, '123456')

    def test_23_parallel_keys_indexing_wrong(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-search-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call3)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>')
        self.assertNotContains(response, 'Friends ID')
        self.assertNotContains(response, '123')
        self.assertNotContains(response, 'Friends Name')
        self.assertNotContains(response, 'Andrew')
        self.assertNotContains(response, 'Iurii Garmash')
        self.assertNotContains(response, 'Employee Name')

    def test_24_additional_docs_adding(self):
        """
        Changes doc1 to new one for consistency.
        Adds additional document 2 and 3 for more complex tests.
        Those docs must be used farther for complex searches.
        """
        # Delete file "doc1" to cleanup after old tests
        url = reverse('api_file', kwargs={'code': doc1,})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # POSTING DOCUMENT 2
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc1_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        self.assertContains(response, 'Friends ID: 123')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', doc1+'.pdf')
        data = { 'file': open(file, 'rb') , 'post_data':'to make this request post type'}
        response = self.client.post(uurl, data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, 'Your document has been indexed successfully')
        self.assertContains(response, 'Friends Name: Andrew')
        self.assertContains(response, 'Start Again')

        # POSTING DOCUMENT 1
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc2_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        self.assertContains(response, 'Friends ID: 321')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', doc2+'.pdf')
        data = { 'file': open(file, 'rb') , 'post_data':'to make this request post type'}
        response = self.client.post(uurl, data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, 'Your document has been indexed successfully')
        self.assertContains(response, 'Friends Name: Yuri')
        self.assertContains(response, 'Start Again')

        # POSTING DOCUMENT 3
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc3_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        self.assertContains(response, 'Friends ID: 222')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', doc3+'.pdf')
        data = { 'file': open(file, 'rb') , 'post_data':'to make this request post type'}
        response = self.client.post(uurl, data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, 'Your document has been indexed successfully')
        self.assertContains(response, 'Friends Name: Someone')
        self.assertContains(response, 'Start Again')

    def test_25_search_by_date_range_only_proper_all_3_docs(self):
        """
        Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays all 3 docs for given date range. (Proper)
        All docs render their indexes correctly.
        Names autogenarated for docs. e.g. ADL-0001, ADL-0002, ADL-0003
        (Not ADL-0001, ADL-0002, ADL-1111 like files uploaded)
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = all3_docs_range
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # 3 documents found
        self.assertContains(response, doc1)
        self.assertContains(response, doc1_dict['description'])
        self.assertContains(response, doc2)
        self.assertContains(response, doc2_dict['description'])
        self.assertContains(response, 'ADL-0003')
        self.assertContains(response, doc3_dict['description'])
        # Context processors provide docrule name
        self.assertContains(response, "Adlibre Invoices")
        # 3 documents secondary keys present
        for doc in [doc1_dict, doc2_dict, doc3_dict]:
            for key in doc.iterkeys():
                if not key=='date' and not key=='description':
                    # Secondary key to test
                    self.assertContains(response, doc[key])
        # Searching keys exist in search results
        self.assertContains(response, '2012-03-30')
        self.assertContains(response, '2012-03-01')
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_26_search_by_date_range_only_proper_2_docs_without_1(self):
        """
        Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays all 2 docs for given date range. (Proper)
        And does not contain doc3 values.
        All docs render their indexes correctly.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = date_range_1and2_not3
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # 3 documents found
        self.assertContains(response, doc1)
        self.assertContains(response, doc1_dict['description'])
        self.assertContains(response, doc2)
        self.assertContains(response, doc2_dict['description'])
        # Context processors provide docrule name
        self.assertContains(response, "Adlibre Invoices")
        # 2 documents secondary keys present
        for doc in [doc1_dict, doc2_dict]:
            for key in doc.iterkeys():
                if not key=='date' and not key=='description':
                    # Secondary key to test
                    self.assertContains(response, doc[key])
        # No unique doc3 keys exist
        self.assertNotContains(response, 'ADL-0003')
        self.assertNotContains(response, doc3_dict['description'])
        self.assertNotContains(response, doc3_dict['Required Date'])
        self.assertNotContains(response, doc3_dict['Friends ID'])
        self.assertNotContains(response, doc3_dict['Friends Name'])
        # Searching keys exist in search results
        self.assertContains(response, '2012-03-20')
        self.assertContains(response, '2012-03-01')
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_27_search_by_date_range_only_proper_3_d_doc_only(self):
        """
        Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc3 only for given date range. (Proper)
        And does not contain doc1 and2 unique values.
        All docs render their indexes correctly.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = date_range_only3
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # 3-d document only found
        self.assertNotContains(response, doc1)
        self.assertNotContains(response, doc2)
        # Context processors provide docrule name
        self.assertContains(response, "Adlibre Invoices")
        # 2 first documents secondary keys NOT present
        for doc in [doc1_dict, doc2_dict]:
            for key in doc.iterkeys():
                if not key in ['Employee Name', 'Friends Name', 'Employee ID']: # Collision with docs 1 and 2
                    # Secondary key to test
                    self.assertNotContains(response, doc[key])
        # Full doc3 data exist
        self.assertContains(response, 'ADL-0003')
        for key in doc3_dict.iterkeys():
            # Secondary key to test
            self.assertContains(response, doc3_dict[key])
        # Searching keys exist in search results
        self.assertContains(response, '2012-03-30')
        self.assertContains(response, '2012-03-25')
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_28_search_by_date_range_no_docs(self):
        """
        Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc3 only for given date range. (Proper)
        And does not contain doc1 and2 unique values.
        All docs render their indexes correctly.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = date_range_none
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # none of 3 documents present in response
        self.assertNotContains(response, doc1)
        self.assertNotContains(response, doc2)
        self.assertNotContains(response, 'ADL-0003')
        # Searching keys exist in search results
        self.assertContains(response, '2012-03-30')
        self.assertContains(response, '2012-03-31')
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_29_search_by_date_range_with_keys_1(self):
        """
        Proper call to search by date range with integer and string keys.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc1 only for given date range and doc1 unique keys. (Proper)
        And does not contain doc2 and3 unique values.
        All docs render their indexes correctly.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        data = self._create_search_dict_for_range_and_keys( date_range_with_keys_doc1,
                                                            ids,
                                                            date_range_with_keys_3_docs,)
        # Searching date range with unique doc1 keys
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # none of 2 other documents present in response
        self.assertNotContains(response, doc2)
        self.assertNotContains(response, 'ADL-0003')
        # Searching keys exist in search results
        self.assertContains(response, date_range_with_keys_3_docs[u'date'])
        self.assertContains(response, date_range_with_keys_3_docs[u'end_date'])
        for key, value in date_range_with_keys_doc1.iteritems():
            self.assertContains(response, value)
        # doc1 data exist in response
        for key, value in doc1_dict.iteritems():
            self.assertContains(response, value)
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_30_search_by_date_range_with_keys_2(self):
        """
        Proper call to search by date range with one key for 2 docs (2 and 3).
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc2 and doc3 for given date range and key. (Proper)
        And does not contain doc1 unique values.
        All docs render their indexes correctly.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        data = self._create_search_dict_for_range_and_keys( date_range_with_keys_doc2,
                                                            ids,
                                                            date_range_with_keys_3_docs,)
        # Searching date range with unique doc1 keys
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # No doc1 document present in response
        self.assertNotContains(response, doc1)
        # Searching keys exist in search results
        self.assertContains(response, date_range_with_keys_3_docs[u'date'])
        self.assertContains(response, date_range_with_keys_3_docs[u'end_date'])
        for key, value in date_range_with_keys_doc2.iteritems():
            self.assertContains(response, value)
        # doc2 and doc3 data exist in response
        for doc_dict in [doc2_dict, doc3_dict]:
            for key, value in doc_dict.iteritems():
                self.assertContains(response, value)
        # Does not contain doc1 unique values
        self.assertNotContains(response, doc1_dict['description'])
        self.assertNotContains(response, doc1_dict['Employee Name']) # Iurii Garmash
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    # TODO: this test must be refactored
    # if issue with secondary key type 'date' will change logic into 'date range' instead of 'exact date', like it is now
    def test_31_search_by_keys_only(self):
        """
        Proper call to search by secondary key exact date key.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc1 for given secondary key of 'date' type. (Proper)
        And does not contain doc2 and doc3 unique values.
        All docs render their indexes correctly.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        # Dict without actual date
        data = self._create_search_dict_for_range_and_keys( date_type_key_doc1,
                                                            ids )
        # Searching date range with unique doc1 keys
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # None of doc2 and doc3 present in response
        self.assertNotContains(response, doc2)
        self.assertNotContains(response, doc3)
        self.assertNotContains(response, doc2_dict['description'])
        self.assertNotContains(response, doc3_dict['description'])
        # Searching keys exist in search results
        for key, value in date_type_key_doc1.iteritems():
            self.assertContains(response, value)
        # doc1 data exist in response
        for key, value in doc1_dict.iteritems():
            self.assertContains(response, value)
        self.assertContains(response, doc1)
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_32_additional_docs_adding_another_docrule(self):
        """
        Adds additional documents 1 and 2 for more complex tests
        with other docrule and another MDT.
        Those docs must be used farther for complex searches and testing JTG behavioural requirements.
        """
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            # Selecting Document Type Rule
            url = reverse('mdtui-index-type')
            response = self.client.post(url, {'docrule': test_mdt_docrule_id2})
            self.assertEqual(response.status_code, 302)
            # Getting indexes form and matching form Indexing Form fields names
            url = reverse('mdtui-index-details')
            response = self.client.get(url)
            rows_dict = self._read_indexes_form(response)
            post_dict = self._convert_doc_to_post_dict(rows_dict, doc_dict)
            # Adding Document Indexes
            response = self.client.post(url, post_dict)
            #print response
            self.assertEqual(response.status_code, 302)
            uurl = self._retrieve_redirect_response_url(response)
            response = self.client.get(uurl)
            # Keys added to indexes
            self.assertContains(response, 'Reporting Entity: '+doc_dict['Reporting Entity'])
            self.assertEqual(response.status_code, 200)
            # Make the file upload
            file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', doc1+'.pdf')
            data = { 'file': open(file, 'rb') , 'post_data':'to make this request post type'}
            response = self.client.post(uurl, data)
            # Follow Redirect
            self.assertEqual(response.status_code, 302)
            new_url = self._retrieve_redirect_response_url(response)
            response = self.client.get(new_url)
            self.assertContains(response, 'Your document has been indexed successfully')
            self.assertContains(response, 'Report Date: '+doc_dict['Report Date'])
            self.assertContains(response, 'Start Again')

    def test_33_search_date_range_withing_2_different_docrules(self):
        """
        MUI search collisions bugs absent.
        Search by date range returns result for docs only from this docrule.
        Search Step 'results' displays proper captured indexes for docrule2 of those tests.
        (MDT3) keys are displayed and MDT's 1 and 2 does not displaying.
        2 test docs for MDT3 rendered.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id2}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, all_docs_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Searching keys exist in search results
        self.assertContains(response, all_docs_range[u'date'])
        self.assertContains(response, all_docs_range[u'end_date'])
        # doc1 and doc2 for MDT3 data exist in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertContains(response, value)
        # Test doc's filenames genrated properly
        self.assertContains(response, 'BBB-0001')
        self.assertContains(response, 'BBB-0002')
        # Does not contain unique values from docs in another docrules
        for doc_dict in [doc1_dict, doc2_dict, doc3_dict]:
            self.assertNotContains(response, doc_dict['description'])
            self.assertNotContains(response, doc_dict['Employee Name'])
        # Keys from MDT-s 1 and 2 not rendered vin search response
        for key in doc1_dict.iterkeys():
            if not key=='date' and not key=='description':
                self.assertNotContains(response, key)

    def test_34_search_date_range_withing_2_different_docrules_2(self):
        """
        MUI search collisions bugs absent.
        Search by date range returns result for docs only from this docrule.
        Search Step 'results' displays proper captured indexes for docrule1 of those tests.
        (MDT1 and MDT2) keys are displayed and MDT3 keys does not displaying.
        3 test docs for MDT1 and MDT2 rendered.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, all_docs_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Searching keys exist in search results
        self.assertContains(response, all_docs_range[u'date'])
        self.assertContains(response, all_docs_range[u'end_date'])
        # doc1, doc2 and doc3 for MDTs 1 and 2 data exist in response
        for doc_dict in [doc1_dict, doc2_dict, doc3_dict]:
            for key, value in doc_dict.iteritems():
                self.assertContains(response, value)
        # Test doc's filenames genrated properly
        self.assertContains(response, 'ADL-0001')
        self.assertContains(response, 'ADL-0002')
        self.assertContains(response, 'ADL-0003')
        # Does not contain unique values from docs in another docrules
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            self.assertNotContains(response, doc_dict['description'])
            self.assertNotContains(response, doc_dict['Reporting Entity'])
        # Keys from MDT-s 1 and 2 not rendered vin search response
        for key in m2_doc1_dict.iterkeys():
            if not key=='date' and not key=='description':
                self.assertNotContains(response, key)

    def test_35_search_date_range_withing_2_different_docrules_with_keys(self):
        """
        MUI search collisions bugs absent.
        Search by date range returns result for docs only from this docrule.
        Search Step 'results' displays proper captured indexes for docrule2 of those tests.
        (MDT3) keys are displayed and MDT's 1 and 2 does not displaying.
        2 test docs for MDT3 rendered.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, all_docs_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Searching keys exist in search results
        self.assertContains(response, all_docs_range[u'date'])
        self.assertContains(response, all_docs_range[u'end_date'])
        # doc1, doc2 and doc3 for MDTs 1 and 2 data exist in response
        for doc_dict in [doc1_dict, doc2_dict, doc3_dict]:
            for key, value in doc_dict.iteritems():
                self.assertContains(response, value)
            # Test doc's filenames genrated properly
        self.assertContains(response, 'ADL-0001')
        self.assertContains(response, 'ADL-0002')
        self.assertContains(response, 'ADL-0003')
        # Does not contain unique values from docs in another docrules
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            self.assertNotContains(response, doc_dict['description'])
            self.assertNotContains(response, doc_dict['Reporting Entity'])
            # Keys from MDT-s 1 and 2 not rendered vin search response
        for key in m2_doc1_dict.iterkeys():
            if not key=='date' and not key=='description':
                self.assertNotContains(response, key)

    def test_36_uppercase_fields(self):
        """
        Adds MDT indexes to test Uppercase fields behaviour.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id3})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        # Wrong uppercase field provided
        post_dict = upper_wrong_dict
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field should be uppercase.')

        # Normal uppercase field rendering and using
        post_dict = upper_right_dict
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        # Assert Indexing file upload step rendered with all keys
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Creation Date: 2012-04-17')
        self.assertContains(response, 'Description: something usefull')
        self.assertContains(response, 'Tests Uppercase Field: UPPERCASE DATA')
        self.assertContains(response, "Your document's indexing keys:")

    def test_z_cleanup(self):
        """
        Cleaning up after all tests finished.
        Must be ran after all tests in this test suite.
        """
        # Deleting all test MDT's
        # (with doccode from var "test_mdt_docrule_id" and "test_mdt_docrule_id2")
        # using MDT's API.
        url = reverse('api_mdt')
        for mdt_ in [test_mdt_docrule_id, test_mdt_docrule_id2, test_mdt_docrule_id3]:
            response = self.client.get(url, {"docrule_id": str(mdt_)})
            data = json.loads(str(response.content))
            for key, value in data.iteritems():
                mdt_id =  data[key]["mdt_id"]
                response = self.client.delete(url, {"mdt_id": mdt_id})
                self.assertEqual(response.status_code, 204)

        # TODO: figure out why running this with list and iteration produces bugs in splitting (doc_codes.models)
        # Delete file "doc1"
        url = reverse('api_file', kwargs={'code': doc1,})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Delete file "doc2"
        url = reverse('api_file', kwargs={'code': doc2,})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Delete file "doc3"
        url = reverse('api_file', kwargs={'code': 'ADL-0003',})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Delete file "doc1" for mdt3
        url = reverse('api_file', kwargs={'code': 'BBB-0001',})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Delete file "doc2" for mdt3
        url = reverse('api_file', kwargs={'code': 'BBB-0002',})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # Compacting CouchDB dmscouch/mdtcouch DB's after tests
        server = Server()
        db1 = server.get_or_create_db("dmscouch")
        db1.compact()
        db2 = server.get_or_create_db("mdtcouch")
        db2.compact()

    def _read_indexes_form(self, response):
        """
        Helper to parse response with Document Indexing Form (MDTUI Indexing Step 2 Form)
        And returns key:value dict of form's dynamical fields for our tests.
        """
        prog = re.compile(indexes_form_match_pattern, re.DOTALL)
        matches_set = prog.findall(str(response))
        matches = {}
        for key,value in matches_set:
            matches[key]=value
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

    def _createa_search_dict(self, doc_dict):
        """
        Creates a search dict to avoid rewriting document dict constants.
        """
        search_dict = {}
        for key in doc_dict.keys():
            search_dict[key] = doc_dict[key]
        return search_dict

    def _create_search_dict_for_range_and_keys(self, keys_dict, form_ids_dict, date_range=None):
        """
        Creates a dict for custom keys to search for date range + some keys
        Takes into account:
          - form dynamic id's
          - date range provided
          - keys provided
        """
        request_dict = {}
        # Adding dates to request
        if date_range:
            for key, value in date_range.iteritems():
                request_dict[key] = value
        else:
            request_dict[u'date'] = u''
            request_dict[u'end_date'] = u''
        # Converting keys data to form id's view
        temp_keys = {}
        for key, value in keys_dict.iteritems():
            temp_keys[form_ids_dict[key]] = value
        # Finally adding converted form numeric field ids with values to request data dict
        for key, value in temp_keys.iteritems():
            request_dict[key] = value
        return request_dict
