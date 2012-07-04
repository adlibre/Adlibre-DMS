"""
Module: MDTUI tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import json, os, urllib, datetime, re

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

from couchdbkit import Server

from adlibre.date_converter import date_standardized
from mdtui.views import MDTUI_ERROR_STRINGS

# auth user
username = 'admin'
password = 'admin'

# test user 1
username_1 = 'test_perms_1'
password_1 = 'test1'

# test user 2
username_2 = 'test_perms_2'
password_2 = 'test2'

couchdb_url = 'http://127.0.0.1:5984'

test_mdt_docrule_id = 2 # should be properly assigned to fixtures docrule that uses CouchDB plugins
test_mdt_docrule_id2 = 7 # should be properly assigned to fixtures docrule that uses CouchDB plugins
test_mdt_docrule_id3 = 8 # should be properly assigned to fixtures docrule that uses CouchDB plugins

test_mdt_id_1 = 1 # First MDT used in testing search part of MUI
test_mdt_id_2 = 2 # Second MDT used in testing search part of MUI
test_mdt_id_3 = 3 # Third MDT used in testing search part of MUI
test_mdt_id_5 = 5 # Last MDT used in testing search part of MUI

indexes_form_match_pattern = '(Employee ID|Employee Name|Friends ID|Friends Name|Required Date|Reporting Entity|Report Date|Report Type|Employee|Tests Uppercase Field).+?name=\"(\d+|\d+_from|\d+_to)\"'

indexing_done_string = 'Your document has been indexed'
indexes_added_string = 'Your documents indexes'
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
            "description": "Report type (e.g. Reconciliation, Pay run etc)"
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

mdt5 = {
    "_id": "mdt5",
    "description": "Test MDT Number 5",
    "docrule_id": [str(test_mdt_docrule_id3), str(test_mdt_docrule_id2)],
    "fields": {
        "1": {
            "field_name": "Employee",
            "description": "testing 1 mdt to 2 docrules",
            "type": "string"
        }
    },
    "parallel": {}
}

# Static dictionary of documents to be indexed for mdt1 and mdt2
doc1_dict = {
    'date': date_standardized('2012-03-06'),
    'description': 'Test Document Number 1',
    'Employee ID': '123456',
    'Required Date': date_standardized('2012-03-07'),
    'Employee Name': 'Iurii Garmash',
    'Friends ID': '123',
    'Friends Name': 'Andrew',
}

doc2_dict = {
    'date': date_standardized('2012-03-20'),
    'description': 'Test Document Number 2',
    'Employee ID': '111111',
    'Required Date': date_standardized('2012-03-21'),
    'Employee Name': 'Andrew Cutler',
    'Friends ID': '321',
    'Friends Name': 'Yuri',
}

doc3_dict = {
    'date': date_standardized('2012-03-28'),
    'description': 'Test Document Number 3',
    'Employee ID': '111111',
    'Required Date': date_standardized('2012-03-29'),
    'Employee Name': 'Andrew Cutler',
    'Friends ID': '222',
    'Friends Name': 'Someone',
}

# Static dictionary of document #1 to test WARNING of creating new index fields
doc1_creates_warnigs_dict = {
    'date': date_standardized('2012-03-06'),
    'description': 'Test Document Number N',
    'Employee ID': '1234567',
    'Required Date': date_standardized('2012-03-07'),
    'Employee Name': 'Iurii Garmash',
    'Friends ID': '123',
    'Friends Name': 'Andrew',
}

doc1_creates_warnigs_string = 'Adding new indexing key: Employee ID: 1234567'

# Static dictionary of documents to be indexed for mdt3
m2_doc1_dict = {
    'date': date_standardized('2012-04-01'),
    'description': 'Test Document MDT 3 Number 1',
    'Reporting Entity': 'JTG',
    'Report Date': date_standardized('2012-04-01'),
    'Report Type': 'Reconciliation',
    'Employee': 'Vovan',
}

m2_doc2_dict = {
    'date': date_standardized('2012-04-03'),
    'description': 'Test Document MDT 3 Number 2',
    'Reporting Entity': 'FCB',
    'Report Date': date_standardized('2012-04-04'),
    'Report Type': 'Pay run',
    'Employee': 'Vovan',
}

m2_doc3_dict = {
    'date': date_standardized('2012-05-01'),
    'description': 'Test Document MDT 3 Number 3',
    'Reporting Entity': 'FCB',
    'Report Date': date_standardized('2012-05-01'),
    'Report Type': 'Pay run',
    'Employee': 'Andrew',
}

ind_doc1 = {
    'date': date_standardized('2012-04-03'),
    'description': 'Test Document MDT 3 Number 2                                 ',
    'Reporting Entity': 'FCB                                            ',
    'Report Date': date_standardized('2012-04-04'),
    'Report Type': '                     Pay run                           ',
}

# Test Documents for MDT 5 (Required to test search displaying data withing multiple Document Type scopes)
m5_doc1_dict = {
    'date': date_standardized('2012-03-10'),
    'description': 'Test Document Number 1 for MDT 5',
    'Employee': 'Andrew',
    'Tests Uppercase Field': 'some data',
}

m5_doc2_dict = {
    'date': date_standardized('2012-03-12'),
    'description': 'Test Document Number 2 for MDT 5',
    'Employee': 'Andrew',
    'Tests Uppercase Field': 'some other data',
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

# Proper for single key
typehead_call4 = {
    'key_name': "Reporting Entity",
    "autocomplete_search": "JT"
}
# Inproper for single key
typehead_call5 = {
    'key_name': "Reporting Entity",
    "autocomplete_search": "11"
}

# Search dates ranges creation from single date testing
range_gen1 = {
    'end_date':date_standardized('2012-04-02'),
    'Report Date From': date_standardized('2012-03-30')
}

# Proper date range calls
all3_docs_range = {
    u'end_date':unicode(date_standardized('2012-03-30')),
    u'1':u'',
    u'0':u'',
    u'3':u'',
    u'2':u'',
    u'4':u'',
    u'date':unicode(date_standardized('2012-03-01')),
}
all_docs_range = {
    u'end_date':unicode(date_standardized('2012-04-30')),
    u'1':u'',
    u'0':u'',
    u'2':u'',
    u'date':unicode(date_standardized('2012-03-01')),
} # Search by docrule2 MDT3
date_range_1and2_not3 = {
    u'end_date':unicode(date_standardized('2012-03-20')),
    u'1':u'',
    u'0':u'',
    u'3':u'',
    u'2':u'',
    u'4':u'',
    u'date':unicode(date_standardized('2012-03-01')),
}
date_range_only3 = {
    u'end_date':unicode(date_standardized('2012-03-30')),
    u'1':u'',
    u'0':u'',
    u'3':u'',
    u'2':u'',
    u'4':u'',
    u'date':unicode(date_standardized('2012-03-25')),
}
date_range_none = {
    u'end_date':unicode(date_standardized('2012-03-31')),
    u'1':u'',
    u'0':u'',
    u'3':u'',
    u'2':u'',
    u'4':u'',
    u'date':unicode(date_standardized('2012-03-30')),
}
all_docs_range_and_key = {
    u'date':unicode(date_standardized('2012-03-01')),
    u'end_date':unicode(date_standardized('2012-05-05')),
    u'0': u'Andrew',
}

# Requests search of BBB-0001 document only specifying date range for it
date_range_withing_2_ranges_1 = {
    u'2_to': [u'03/04/2012'],
    u'end_date': [u'05/04/2012'],
    u'2_from': [u'01/04/2012'],
    u'1': [u''],
    u'0': [u''],
    u'3': [u''],
    u'date': [u'01/04/2012'],
}


# Proper date range with keys search
date_range_with_keys_3_docs = {
    u'date':unicode(date_standardized('2012-03-01')),
    u'end_date':unicode(date_standardized('2012-03-30')),
} # Date range for 3 docs
date_range_with_keys_doc1 = {
    u'Friends ID': u'123',
    u'Friends Name': u'Andrew',
} # Unique keys for doc1
date_range_with_keys_doc2 = {
    u'Friends Name': u'Yuri',
} # Unique keys for docs 2 and 3
date_type_key_doc1 = {
    u'Required Date': unicode(date_standardized('2012-03-07')),
} # Unique date type key for doc 1

# Uppercase fields
upper_wrong_dict = {
    u'date': [unicode(date_standardized('2012-04-17'))],
    u'0': [u'lowercase data'],
    u'description': [u'something usefull']
}
upper_right_dict = {
    u'date': [unicode(date_standardized('2012-04-17'))],
    u'0': [u'UPPERCASE DATA'],
    u'description': [u'something usefull']
}

# TODO: test proper CSV export, even just simply, with date range and list of files present there
# TODO: add tests fo date ranges searches.
# TODO: add tests for Typehead suggests values between docrules

# TODO: test posting docs to 2 different document type rules and mix out parallel keys and normal search here for proper behaviour:
# THIS IS WRONG:
# 1. search does not filter on MDT correctly. Getting results from multiple MDTs (and document types).
# 2. parallel key lookups are not sharing parallel info across document types.

class MDTUI(TestCase):

    def setUp(self):
        # We are using only logged in client in this test
        self.client.login(username=username, password=password)

    def test_00_setup_mdts(self):
        """
        Setup all MDTs for the test suite.
        Made it standalone test because we need it to be run only once
        """
        # adding our MDT's required through API. (MDT API should be working)
        url = reverse('api_mdt')
        # List formatted so to comment out any MDT easily
        for m in [
                    mdt1,
                    mdt2,
                    mdt3,
                    mdt4,
                    mdt5
                 ]:
            mdt = json.dumps(m)
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
        self.assertContains(response, 'Creation Date: %s' % date_standardized('2012-03-06'))
        self.assertContains(response, 'Employee ID: 123456')
        self.assertContains(response, 'Employee Name: Iurii Garmash')
        self.assertContains(response, 'Required Date: %s' % date_standardized('2012-03-07'))
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
        data = { 'file': open(file, 'rb'), 'uploaded':u''}
        response = self.client.post(url+'?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, indexing_done_string)
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
        self.assertContains(response, 'mdt1')
        self.assertContains(response, 'mdt2')
        self.assertContains(response, 'mdt3')
        self.assertContains(response, 'mdt4')
        self.assertContains(response, 'mdt5')
        self.assertContains(response, 'Document Search')
        self.assertEqual(response.status_code, 200)

    def test_10_search_indexes_warning(self):
        """
        Testing Search part Warning for indexes.
        """
        url = reverse('mdtui-search-options')
        response = self.client.get(url)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_MDTS'])
        self.assertEqual(response.status_code, 200)

    def test_11_search_results_warning(self):
        """
        Testing Search part  warning for results.
        """
        url = reverse('mdtui-search-results')
        response = self.client.get(url)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        self.assertEqual(response.status_code, 200)

    def test_12_search_docrule_select_improper_call(self):
        """
        Makes wrong request to view. Response returns back to docrule selection.
        """
        url = reverse('mdtui-search-type')
        response = self.client.post(url)
        self.assertContains(response, 'mdt1')
        self.assertEqual(response.status_code, 200)

    def test_13_search_MDT_selection(self):
        """
        Proper Searching call.
        """
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # checking for proper fields rendering
        self.assertContains(response, "Creation Date From")
        self.assertContains(response, "Creation Date To")
        self.assertContains(response, "Required Date From")
        self.assertContains(response, "Required Date To")
        self.assertContains(response, "Friends ID")
        self.assertContains(response, "Friends Name")
        self.assertNotContains(response, "Description</label>")
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['NO_MDTS'])
        self.assertEqual(response.status_code, 200)

    def test_14_search_by_date_proper(self):
        """
        Proper call to search by date.
        MDTUI Search By Indexes Form parses data properly.
        Search Step 3 displays proper captured indexes.
        """
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1 Indexes
        response = self.client.post(url, {'date': doc1_dict["date"], 'end_date': '', '0':'', '1':'', '2_from':'', '2_to':''})
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
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # assigning form fields
        url = reverse('mdtui-search-options')
        response = self.client.get(url)
        # Getting indexes form and matching form Indexing Form fields names
        rows_dict = self._read_indexes_form(response)
        search_dict = self._create_search_dict_range_and_keys_for_search(doc1_dict, rows_dict)
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
        date_str = datetime.datetime.strftime(date_req, settings.DATE_FORMAT)
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
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
        self.assertContains(response, date_standardized('2012-03-06')) # docs data populated into form
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
        # Selecting MDT
        url = reverse('mdtui-search-type')
        response = self.client.post(url, {'mdt': test_mdt_id_1})
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
        response = self.client.post(url, {'mdt': test_mdt_id_2})
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
        response = self.client.post(url, {'mdt': test_mdt_id_1})
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
        data = { 'file': open(file, 'rb') , 'uploaded':u''}
        response = self.client.post(uurl+'?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, indexing_done_string)
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
        data = { 'file': open(file, 'rb') , 'uploaded':u''}
        response = self.client.post(uurl+'?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, indexing_done_string)
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
        data = { 'file': open(file, 'rb') , 'uploaded':u''}
        response = self.client.post(uurl+'?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, indexing_done_string)
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
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
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
        self.assertContains(response, date_standardized('2012-03-30'))
        self.assertContains(response, date_standardized('2012-03-01'))
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
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
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
        self.assertContains(response, date_standardized('2012-03-20'))
        self.assertContains(response, date_standardized('2012-03-01'))
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
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
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
        self.assertContains(response, date_standardized('2012-03-30'))
        self.assertContains(response, date_standardized('2012-03-25'))
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
        # Setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
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
        self.assertContains(response, date_standardized('2012-03-30'))
        self.assertContains(response, date_standardized('2012-03-31'))
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
        # Setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
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
        data = {'mdt': test_mdt_id_1}
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
        for doc_dict in [doc2_dict]:
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

    def test_32_additional_docs_adding_another_docrule(self):
        """
        Adds additional documents 1 and 2 for more complex tests
        with other docrule and another MDT.
        Those docs must be used farther for complex searches and testing JTG behavioural requirements.
        """
        for doc_dict in [m2_doc1_dict, m2_doc2_dict, m2_doc3_dict]:
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
            data = { 'file': open(file, 'rb'), 'uploaded': u''}
            response = self.client.post(uurl+'?uploaded', data)
            # Follow Redirect
            self.assertEqual(response.status_code, 302)
            new_url = self._retrieve_redirect_response_url(response)
            response = self.client.get(new_url)
            self.assertContains(response, indexing_done_string)
            self.assertContains(response, 'Report Date: '+doc_dict['Report Date'])
            self.assertContains(response, 'Start Again')

    def test_33_search_date_range_withing_2_different_docrules(self):
        """
        MUI search collisions bugs absent.
        Search by date range returns result for docs only from this MDT.
        Search Step 'results' displays proper captured indexes for docrule2 of those tests.
        (MDT3) keys are displayed and MDT's 1 and 2 does not displaying.
        2 test docs for MDT3 rendered.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_3}
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

    def test_34_additional_docs_adding_third_docrule(self):
        """
        Adds additional documents 1 and 2 for more complex tests
        with Document Type 3 and another MDTs.
        Those docs must be used farther for complex searches and testing JTG behavioural requirements.
        """
        for doc_dict in [m5_doc1_dict, m5_doc2_dict]:
            # Selecting Document Type Rule
            url = reverse('mdtui-index-type')
            response = self.client.post(url, {'docrule': test_mdt_docrule_id3})
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
            self.assertContains(response, 'Description: Test Document Number')
            self.assertEqual(response.status_code, 200)
            # Make the file upload
            file = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', doc1+'.pdf')
            data = { 'file': open(file, 'rb'), 'uploaded': u''}
            response = self.client.post(uurl+'?uploaded', data)
            # Follow Redirect
            self.assertEqual(response.status_code, 302)
            new_url = self._retrieve_redirect_response_url(response)
            response = self.client.get(new_url)
            self.assertContains(response, indexing_done_string)
            self.assertContains(response, 'Employee: '+doc_dict['Employee'])
            self.assertContains(response, 'Start Again')

    def test_35_search_date_range_withing_2_different_docrules_2(self):
        """
        MUI search collisions bugs absent.
        Search by date range returns result for docs only from this docrule.
        Search Step 'results' displays proper captured indexes for docrule1 of those tests.
        (MDT1 and MDT2) keys are displayed and MDT3 keys does not displaying.
        3 test docs for MDT1 and MDT2 rendered.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_5}
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
        # doc1, doc2 for MDTs 2 and 3 data exist in response
        for doc_dict in [m5_doc1_dict, m5_doc2_dict, m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                # Uppercase value hack
                if value=='some data' or value=='some other data':
                    value = value.upper()
                self.assertContains(response, value)
        # Test doc's filenames genrated properly
        self.assertContains(response, 'CCC-0001')
        self.assertContains(response, 'CCC-0002')
        self.assertContains(response, 'BBB-0001')
        self.assertContains(response, 'BBB-0002')
        # Does not contain another docs
        self.assertNotContains(response, 'ADL-0001')
        self.assertNotContains(response, 'ADL-0002')
        self.assertNotContains(response, 'ADL-0003')

    def test_36_search_date_range_withing_2_different_docrules_with_keys(self):
        """
        MUI search collisions bugs absent.
        Search by date range returns result for docs only from this docrule.
        Search Step 'results' displays proper captured indexes for docrule2 of those tests.
        (MDT3) keys are displayed and MDT's 1 and 2 does not displaying.
        2 test docs for MDT3 rendered.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, all_docs_range_and_key)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Searching keys exist in search results
        self.assertContains(response, all_docs_range_and_key[u'date'])
        self.assertContains(response, all_docs_range_and_key[u'end_date'])
        # doc1, doc2 for MDTs 2 and 3 data exist in response
        for doc_dict in [m5_doc1_dict, m5_doc2_dict, m2_doc3_dict]:
            for key, value in doc_dict.iteritems():
                # Uppercase value hack
                if value=='some data' or value=='some other data':
                    value = value.upper()
                self.assertContains(response, value)
            # Test doc's filenames genrated properly
        self.assertContains(response, 'CCC-0001')
        self.assertContains(response, 'CCC-0002')
        self.assertContains(response, 'BBB-0003')
        # Does not contain another docs
        self.assertNotContains(response, 'ADL-0001')
        self.assertNotContains(response, 'ADL-0002')
        self.assertNotContains(response, 'ADL-0003')
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_37_uppercase_fields_lowercase_data(self):
        """
        Adds MDT indexes to test Uppercase fields behaviour.
        """
        # Lowercase field provided
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id3})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        post_dict = upper_wrong_dict
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Creation Date: %s' % date_standardized('2012-04-17'))
        self.assertContains(response, 'Description: something usefull')
        self.assertContains(response, 'Tests Uppercase Field: LOWERCASE DATA')
        self.assertContains(response,indexes_added_string)

    def test_38_uppercase_fields_UPPERCASE_DATA(self):
        # Normal uppercase field rendering and using
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id3})
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-details')
        post_dict = upper_right_dict
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        # Assert Indexing file upload step rendered with all keys
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Creation Date: %s' % date_standardized('2012-04-17'))
        self.assertContains(response, 'Description: something usefull')
        self.assertContains(response, 'Tests Uppercase Field: UPPERCASE DATA')
        self.assertContains(response, indexes_added_string)

    def test_39_search_by_keys_only_contains_secondary_date_range(self):
        """
        Proper call to search by secondary key date range key.
        MDTUI Search By Search Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc1 for given secondary key of 'date' type. (Proper)
        And does not contain doc2 and doc3 unique values.
        All docs render their indexes correctly.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        # Dict without actual date
        data = self._create_search_dict_range_and_keys_for_search( date_type_key_doc1,
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
            date_key = False
            try:
                date_key = datetime.datetime.strptime(value, settings.DATE_FORMAT)
            except ValueError:
                pass
            if date_key and not key == 'date':
                from_date = date_key - datetime.timedelta(days=1)
                to_date = date_key + datetime.timedelta(days=1)
                value1 = from_date.strftime(settings.DATE_FORMAT)
                value2 = to_date.strftime(settings.DATE_FORMAT)
                self.assertContains(response, value1)
                self.assertContains(response, value2)
            else:
                self.assertContains(response, value)
        self.assertContains(response, doc1)
        # docs for mdt3 does not present in response
        for doc_dict in [m2_doc1_dict, m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, 'BBB-0001')
        self.assertNotContains(response, 'BBB-0002')

    def test_40_autocomplete_single_key(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        Single key must be returned.
        Must render suggestion for this key only.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id2})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call4)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporting Entity')
        self.assertContains(response, 'JTG')

    def test_41_autocomplete_single_key_wrong(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        Single key must be returned.
        Must render suggestion for this key only.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id2})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call5)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Reporting Entity')
        self.assertNotContains(response, 'JTG')

    def test_42_trim_whitespaces_works_on_all_fields(self):
        """
        All fields should trim whitespaces upon submitting indexes form
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id2})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, ind_doc1)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        #print response
        self.assertEqual(response.status_code, 200)
        # Keys added to indexes
        self.assertNotContains(response, 'Reporting Entity: '+ind_doc1['Reporting Entity'])
        self.assertContains(response, 'Reporting Entity: '+ind_doc1['Reporting Entity'].strip(' \t\n\r'))

    def test_43_date_keys_converted_to_date_ranges_on_search(self):
        """
        Date keys provided converted to date ranges with start/end date period
        for both document indexing date/secondary dates key types.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_3}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        data = {}
        for key, value in range_gen1.iteritems():
            if not key == 'date' and not key == 'end_date':
                data[ids[key]] = value
            else:
                data[key] = value
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
        # Things that should be here
        self.assertContains(response, date_standardized('2100-01-01')) # Max date range
        self.assertContains(response, date_standardized('1960-01-01')) # Min date range
        self.assertContains(response, date_standardized('2012-04-02'))
        report_string = 'Report Date: (from: %s to: %s)' % (date_standardized('2012-03-30'), date_standardized('2100-01-01'))
        self.assertContains(response, report_string)# Range recognised properly
        self.assertContains(response, 'BBB-0001')
        self.assertContains(response, 'BBB-0002')
        self.assertContains(response, 'BBB-0003')

    def test_44_warns_about_new_parallel_key(self):
        """
        Warns about new parallel keys created
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, doc1_creates_warnigs_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertContains(response, 'Friends ID: 123')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, doc1_creates_warnigs_string)

    def test_45_extended_date_ranges_test(self):
        """
        Testing search files in different date range combinations

        this test tests:
        2 docs for test docrule 2 (BBB-00X)
        filtered by creation date range (creation date)
        without other keys.
        Specifying another date range combinations (secondary keys of "date" type)
        does not break this indexing date filtering.
        """
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': test_mdt_id_3}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        # Searching date range with unique doc1 keys
        response = self.client.post(url, date_range_withing_2_ranges_1)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and only one doc persists there
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BBB-0001')
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # None of doc2 of this docrule and docs from other docrules exist in response
        self.assertNotContains(response, doc1)
        self.assertNotContains(response, doc2)
        self.assertNotContains(response, doc3)
        self.assertNotContains(response, 'BBB-0002')

    def test_46_security_restricts_search_or_index(self):
        # We need another logged in user for this test
        self.client.logout()
        self.client.login(username=username_1, password=password_1)
        # Trying to access indexing
        search_url = reverse('mdtui-search-type')
        index_url = reverse('mdtui-index-type')
        # User test1 have access to search
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, 200)
        # User test1 do not have access to index
        response = self.client.get(index_url)
        self.assertNotEqual(response.status_code, 200)
        self.client.logout()
        self.client.login(username=username_2, password=password_2)
        # User test2 have access to index
        response = self.client.get(index_url)
        self.assertEqual(response.status_code, 200)
        # User test2 do not have access to search
        response = self.client.get(search_url)
        self.assertNotEqual(response.status_code, 200)
        self.client.logout()

    def test_47_indexing_mdt_choices_limited_by_permitted_docrules(self):
        # We need another logged in user for this test
        self.client.logout()
        self.client.login(username=username_1, password=password_1)
        # Checking if user sees his own permitted document type rules
        url = reverse('mdtui-search-type')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mdt3')
        self.assertContains(response, 'mdt4')
        self.assertContains(response, 'mdt5')
        # And does not see hidden ones
        self.assertNotContains(response, 'mdt1')
        self.assertNotContains(response, 'mdt2')
        self.client.logout()

    def test_48_searching_docrule_choices_limited_by_permission(self):
        # We need another logged in user for this test
        self.client.logout()
        self.client.login(username=username_2, password=password_2)
        # Checking if user sees his own permitted document type rules
        url = reverse('mdtui-index-type')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adlibre Invoices')
        self.assertContains(response, 'Test PDFs')
        # And does not see hidden ones
        self.assertNotContains(response, 'Test Doc Type 2')
        self.client.logout()

    def test_49_admin_sees_all_docrules_everywhere(self):
        search_url = reverse('mdtui-search-type')
        index_url = reverse('mdtui-index-type')
        response = self.client.get(index_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Doc Type 2')
        self.assertContains(response, 'Test Doc Type 3')
        self.assertContains(response, 'Adlibre Invoices')
        self.assertContains(response, 'Test PDFs')
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mdt1')
        self.assertContains(response, 'mdt2')
        self.assertContains(response, 'mdt3')
        self.assertContains(response, 'mdt4')
        self.assertContains(response, 'mdt5')

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

        # Deleting all docs used in tests
        for argument in [doc1, doc2, 'ADL-0003', 'BBB-0001', 'BBB-0002', 'BBB-0003', 'CCC-0001', 'CCC-0002']:
            url = reverse('api_file', kwargs={'code': argument,})
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
            if value.endswith('_from'):
                matches[key+' From']=value
            elif value.endswith('_to'):
                matches[key+' To']=value
            else:
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

    def _create_search_dict_range_and_keys_for_search(self, keys_dict, form_ids_dict, date_range=None):
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
            date_key = False
            try:
                date_key = datetime.datetime.strptime(value, settings.DATE_FORMAT)
            except ValueError:
                pass
            if date_key and not key == 'date' and not key == 'end_date':
                key1 = key + ' From'
                key2 = key + ' To'
                from_date = date_key - datetime.timedelta(days=1)
                to_date = date_key + datetime.timedelta(days=1)
                value1 = from_date.strftime(settings.DATE_FORMAT)
                value2 = to_date.strftime(settings.DATE_FORMAT)
                temp_keys[form_ids_dict[key1]] = value1
                temp_keys[form_ids_dict[key2]] = value2
            else:
                if not key == 'description'and not key == 'date' and not key == 'end_date':
                    try:
                        temp_keys[form_ids_dict[key]] = value
                    except KeyError:
                        # key does not present in form
                        pass
        # Finally adding converted form numeric field ids with values to request data dict
        for key, value in temp_keys.iteritems():
            request_dict[key] = value
        return request_dict
