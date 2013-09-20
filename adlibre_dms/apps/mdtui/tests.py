"""
Module: MDTUI tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

import json
import os
import urllib
import datetime
import re

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from couchdbkit import Server

from adlibre.date_converter import date_standardized
from mdtui.views import MDTUI_ERROR_STRINGS
from mdtui.security import SEC_GROUP_NAMES
from mdtui.templatetags.paginator_tags import rebuild_sequence_digg
from mdtcouch.models import MetaDataTemplate
from dmscouch.models import CouchDocument
from core.search import SEARCH_ERROR_MESSAGES
from doc_codes.models import DocumentTypeRule

# TODO: test password reset forms/stuff

# TODO: test proper CSV export, even just simply, with date range and list of files present there
# TODO: add tests for Typeahead suggests values between docrules


class MUITestData(TestCase):
    """Base tests class for MUI interface. Contains basic tests data and strings
       that are not test specific. Inherit in your MUI tests."""

    def __init__(self, *args, **kwargs):
        super(MUITestData, self).__init__(*args, **kwargs)

        self.test_document_files_dir = os.path.join(settings.FIXTURE_DIRS[0], 'testdata')

        # Auth USER
        self.username = 'admin'
        self.password = 'admin'

        # test user 1
        self.username_1 = 'test_perms_1'
        self.password_1 = 'test1'

        # test user 2
        self.username_2 = 'test_perms_2'
        self.password_2 = 'test2'

        # test user 4
        self.username_4 = 'tests_user_4'
        self.password_4 = 'test4'

        # Couchdb data location
        self.couchdb_url = 'http://127.0.0.1:5984'
        self.couchdb_name = 'dmscouch_test'
        self.couchdb_mdts_name = 'mdtcouch_test'

        self.doc1 = 'ADL-0001'
        self.doc2 = 'ADL-0002'
        self.doc3 = 'ADL-0003'
        self.doc4 = 'ADL-0004'
        self.edit_document_name_1 = 'CCC-0001'
        self.edit_document_name_2 = 'BBB-0001'
        self.edit_document_name_3 = 'BBB-0002'
        self.edit_document_name_4 = 'CCC-0002'
        self.edit_document_name_5 = 'BBB-0003'
        self.edit_document_name_6 = 'CCC-0003'
        self.edit_document_name_7 = 'BBB-0004'

        self.test_mdt_docrule_id = 2  # should be properly assigned to fixtures docrule that uses CouchDB plugins
        self.test_mdt_docrule_id2 = 7  # should be properly assigned to fixtures docrule that uses CouchDB plugins
        self.test_mdt_docrule_id3 = 8  # should be properly assigned to fixtures docrule that uses CouchDB plugins
        self.test_mdt_docrule_id4 = 9  # Barcode docrule

        self.test_mdt_id_1 = 1  # First MDT used in testing search part of MUI
        self.test_mdt_id_2 = 2  # Second MDT used in testing search part of MUI
        self.test_mdt_id_3 = 3  # Third MDT used in testing search part of MUI
        self.test_mdt_id_5 = 5  # Last MDT used in testing search part of MUI
        self.test_mdt_id_6 = 6  # Last MDT used in testing search part of MUI

        ############################ GENERATING REGEXP ##############################
        # to match page form and view it's fields.
        indexes_match_strings = [
            'Employee ID',
            'Employee Name',
            'Friends ID',
            'Friends Name',
            'Required Date',
            'Reporting Entity',
            'Report Date',
            'Report Type',
            'Employee',
            'Tests Uppercase Field',
            'Additional',
            'Chosen Field',
        ]
        main_form_match_regexp = ').+?name=\"(\d+|\d+_from|\d+_to)\"'
        indexes_form_match_pattern = ''
        for index in indexes_match_strings:
            indexes_form_match_pattern += index + '|'
        indexes_form_match_pattern = indexes_form_match_pattern[:-1]
        self.indexes_form_match_pattern = '(%s%s' % (indexes_form_match_pattern, main_form_match_regexp)
        ################################# END #######################################

        self.indexing_done_string = 'Your document has been indexed'
        self.indexes_added_string = 'Your documents indexes'
        # Searches with Document Type preselected:
        self.select_docrule_2 = {u'docrule': [u'2']}
        self.select_mdt5 = {u'mdt': [u'5']}
        self.select_docrule_7 = {u'docrule': [u'7']}

        # Typeahead calls Proper for doc1
        self.typehead_call1 = {
            'key_name': 'Friends ID',
            'autocomplete_search': '123'
        }
        self.typehead_call2 = {
            'key_name': 'Employee ID',
            'autocomplete_search': '123'
        }
        # Typeahead calls Improper for doc1
        self.typehead_call3 = {
            'key_name': 'Employee ID',
            'autocomplete_search': 'And'
        }

        # Indexes form requests
        self.date_range_all_ADL = {
            u'2_to': [u''],
            u'end_date': [u''],
            u'2_from': [u''],
            u'1': [u''],
            u'0': [u''],
            u'3': [u''],
            u'date': [u'01/01/2012'],
        }
        self.all_docs_range = {
            u'end_date': unicode(date_standardized('2012-04-30')),
            u'1': u'',
            u'0': u'',
            u'2': u'',
            u'date': unicode(date_standardized('2012-03-01')),
        }  # Search by docrule2 MDT3
        self.date_range_1and2_not3 = {
            u'end_date': unicode(date_standardized('2012-03-20')),
            u'1': u'',
            u'0': u'',
            u'3': u'',
            u'2': u'',
            u'4': u'',
            u'date': unicode(date_standardized('2012-03-01')),
        }
        self.date_range_none = {
            u'end_date': unicode(date_standardized('2012-03-31')),
            u'1': u'',
            u'0': u'',
            u'3': u'',
            u'2': u'',
            u'4': u'',
            u'date': unicode(date_standardized('2012-03-30')),
        }
        self.search_MDT_5 = {
            u'0': u'Andrew',
            u'date': u'',
            u'end_date': u'',
        }
        # Date range for 3 docs
        self.date_range_with_keys_3_docs = {
            u'date': unicode(date_standardized('2012-03-01')),
            u'end_date': unicode(date_standardized('2012-03-30')),
        }
        ############################ Documents used in tests ###############################
        # Static dictionary of documents to be indexed for mdt1 and mdt2
        self.doc1_dict = {
            'date': date_standardized('2012-03-06'),
            'description': 'Test Document Number 1',
            'Employee ID': '123456',
            'Required Date': date_standardized('2012-03-07'),
            'Employee Name': 'Iurii Garmash',
            'Friends ID': '123',
            'Friends Name': 'Andrew',
            'Additional': 'Something for 1',
        }
        self.doc2_dict = {
            'date': date_standardized('2012-03-20'),
            'description': 'Test Document Number 2',
            'Employee ID': '111111',
            'Required Date': date_standardized('2012-03-21'),
            'Employee Name': 'Andrew Cutler',
            'Friends ID': '321',
            'Friends Name': 'Yuri',
            'Additional': 'Something for 2',
        }
        self.doc3_dict = {
            'date': date_standardized('2012-03-28'),
            'description': 'Test Document Number 3',
            'Employee ID': '111111',
            'Required Date': date_standardized('2012-03-29'),
            'Employee Name': 'Andrew Cutler',
            'Friends ID': '222',
            'Friends Name': 'Someone',
            'Additional': 'Something for 3',
        }
        self.doc4_barcode_dict = {
            'date': date_standardized('2012-03-06'),
            'description': 'Test Document Number 4',
            'Employee ID': '123456',
            'Required Date': date_standardized('2012-03-07'),
            'Employee Name': 'Iurii Garmash',
            'Friends ID': '123',
            'Friends Name': 'Andrew',
            'Additional': 'Something for 4',
        }
        # Static dictionary of documents to be indexed for mdt3
        self.m2_doc1_dict = {
            'date': date_standardized('2012-04-01'),
            'description': 'Test Document MDT 3 Number 1',
            'Reporting Entity': 'JTG',
            'Report Date': date_standardized('2012-04-01'),
            'Report Type': 'Reconciliation',
            'Employee': 'Vovan',
            'Additional': 'Something mdt2 1',
        }
        self.m2_doc2_dict = {
            'date': date_standardized('2012-04-03'),
            'description': 'Test Document MDT 3 Number 2',
            'Reporting Entity': 'FCB',
            'Report Date': date_standardized('2012-04-04'),
            'Report Type': 'Pay run',
            'Employee': 'Vovan',
            'Additional': 'Something mdt2 2',
        }
        self.m2_doc3_dict = {
            'date': date_standardized('2012-05-01'),
            'description': 'Test Document MDT 3 Number 3',
            'Reporting Entity': 'FCB',
            'Report Date': date_standardized('2012-05-01'),
            'Report Type': 'Pay run',
            'Employee': 'Andrew',
            'Additional': 'Something mdt2 3',
        }
        # Test Documents for MDT 5 (Required to test search displaying data withing multiple Document Type scopes)
        self.m5_doc1_dict = {
            'date': date_standardized('2012-03-10'),
            'description': 'Test Document Number 1 for MDT 5',
            'Employee': 'Andrew',
            'Tests Uppercase Field': 'some data',
            'Chosen Field': "3",
        }
        self.m5_doc2_dict = {
            'date': date_standardized('2012-03-12'),
            'description': 'Test Document Number 2 for MDT 5',
            'Employee': 'Andrew',
            'Tests Uppercase Field': 'some other data',
            'Chosen Field': "4",
        }
        # Modified doc1 dict for testing fixed choice indexes
        self.doc1_dict_forbidden_indexes = {
            'date': date_standardized('2012-03-06'),
            'description': 'Test Document Number 1',
            'Employee ID': '1234567890',
            'Required Date': date_standardized('2012-03-07'),
            'Employee Name': 'Someone Special',
            'Friends ID': '123',
            'Friends Name': 'Andrew',
            'Additional': 'Something for 1',
        }
        # Modified doc1 dict for testing fixed choice indexes
        self.doc1_dict_existing_indexes = {
            'date': date_standardized('2012-03-06'),
            'description': 'Test Document Number 1',
            'Employee ID': '1234567890',
            'Required Date': date_standardized('2012-03-07'),
            'Employee Name': "Andrew Cutler",
            'Friends ID': '123',
            'Friends Name': 'Andrew',
            'Additional': 'Something for 1',
        }
        ################################## END documents ###################################

        ############################ MDTS used in those tests ##############################
        self.mdt1 = {
            "_id": 'mdt1',
            "docrule_id": [str(self.test_mdt_docrule_id), ],
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
                    "description": "Name of tests person",
                    "edit": "locked"
                },
                "3": {
                    "type": "date",
                    "field_name": "Required Date",
                    "description": "Testing Date Type Secondary Key"
                },
            },
            "parallel": {
                "1": ["1", "2"],
            }
        }
        self.mdt2 = {
            "_id": 'mdt2',
            "docrule_id": [str(self.test_mdt_docrule_id), ],
            "description": "Test MDT Number 2",
            "fields": {
                "1": {
                    "type": "integer",
                    "field_name": "Employee ID",
                    "description": "Unique (Staff) ID of the person associated with the document",
                },
                "2": {
                    "type": "string",
                    "field_name": "Employee Name",
                    "description": "Name of the person associated with the document",
                },
            },
            "parallel": {
                "1": ["1", "2"],
            }
        }
        self.mdt3 = {
            "_id": 'mdt3',
            "docrule_id": [str(self.test_mdt_docrule_id2), ],
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
        self.mdt4 = {
            "_id": 'mdt4',
            "docrule_id": [str(self.test_mdt_docrule_id3), ],
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
        self.mdt5 = {
            "_id": "mdt5",
            "description": "Test MDT Number 5",
            "docrule_id": [str(self.test_mdt_docrule_id3), str(self.test_mdt_docrule_id2)],
            "fields": {
                "1": {
                    "field_name": "Employee",
                    "description": "testing 1 mdt to 2 docrules",
                    "type": "string"
                }
            },
            "parallel": {}
        }
        self.mdt6 = {
            "_id": "mdt6",
            "description": "Test MDT 6",
            "docrule_id": [str(self.test_mdt_docrule_id), str(self.test_mdt_docrule_id2)],
            "fields": {
                "1": {
                    "field_name": "Additional",
                    "description": "shouldd have 2 docrules but include Adlibre invoi.... and so on",
                    "type": "string"
                }
            },
            "parallel": {}
        }
        self.mdt7 = {
            "_id": "mdt7",
            "description": "Test MDT 7",
            "docrule_id": [str(self.test_mdt_docrule_id3), ],
            "fields": {
                "1": {
                    "field_name": "Chosen Field",
                    "description": "defines fixed amount of choices",
                    "type": "choice",
                    "choices": ["choice one", "choice two", "choice three", "choice four", "choice 5"]
                }
            },
            "parallel": {}
        }
        self.mdt8 = {
            "_id": "mdt8",
            "description": "Test MDT 9 - Empty indexes",
            "docrule_id": [str(self.test_mdt_docrule_id4)],
            "fields": {},
            "parallel": {}
        }
        #################################### END of MDTS ###################################

    def _read_indexes_form(self, response):
        """Helper to parse response with Document Indexing Form (MDTUI Indexing Step 2 Form)
        And returns key:value dict of form's dynamical fields for our tests."""
        prog = re.compile(self.indexes_form_match_pattern, re.DOTALL)
        matches_set = prog.findall(str(response))
        matches = {}
        for key, value in matches_set:
            if value.endswith('_from'):
                matches[key+' From'] = value
            elif value.endswith('_to'):
                matches[key+' To'] = value
            else:
                matches[key] = value
        return matches

    def _convert_doc_to_post_dict(self, matches, doc):
        """Helper to convert Tests Documents into proper POST dictionary for Indexing Form testing."""
        post_doc_dict = {}
        for key, value in doc.iteritems():
            if key in matches.keys():
                post_doc_dict[matches[key]] = value
            else:
                post_doc_dict[key] = value
        return post_doc_dict

    def _retrieve_redirect_response_url(self, response):
        """helper parses 302 response object.
        Returns redirect url, parsed by regex."""
        self.assertEqual(response.status_code, 302)
        new_url = re.search("(?P<url>https?://[^\s]+)", str(response)).group("url")
        return new_url

    def _createa_search_dict(self, doc_dict):
        """Creates a search dict to avoid rewriting document dict constants."""
        search_dict = {}
        for key in doc_dict.keys():
            search_dict[key] = doc_dict[key]
        return search_dict

    def _create_search_dict_for_range_and_keys(self, keys_dict, form_ids_dict, date_range=None):
        """Creates a dict for custom keys to search for date range + some keys
        Takes into account:
          - form dynamic id's
          - date range provided
          - keys provided"""
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
        """Creates a dict for custom keys to search for date range + some keys
        Takes into account:
          - form dynamic id's
          - date range provided
          - keys provided"""
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

    def _create_edit_indexes_post_dict(self, keys_dict, form_ids_dict):
        """Creates a dict for custom keys to edit document indexes.
        Takes into account:
          - form dynamic id's
          - description provided"""
        request_dict = {}
        for key, value in keys_dict.iteritems():
            if key == 'description':
                request_dict[key] = value
            else:
                request_dict[form_ids_dict[key]] = value
        return request_dict

    def _check_edit_indexes_data_form(self, response, doc_dict):
        """Scans Document edit indexes form for proper data and fields rendering."""
        for field_name, field_value in doc_dict.iteritems():
            if not field_name in ['date', 'description']:
                self.assertContains(response, field_name)
                # Omitting Uppercase field value exception
                if not field_value == 'some data':
                    self.assertContains(response, field_value)
                else:
                    self.assertContains(response, field_value.upper())
            elif field_name == 'description':
                self.assertContains(response, "Description")
                self.assertContains(response, field_value)

    def _check_edit_step_with_document(self, doc_name, doc_dict):
        """
        Subtest...

        Checks for document dict and name rendered properly in indexing - Edit indexes step.
        It creates self.response with form data rendered.
        """
        url = reverse('mdtui-edit', kwargs={'code': doc_name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, doc_name)
        self._check_edit_indexes_data_form(response, doc_dict)
        self.response = response

    def _open_couchdoc(self, db_name, barcode, view_name='_all_docs'):
        """Open given document in a given CouchDB database"""
        firstdoc = {}
        server = Server()
        db = server.get_or_create_db(db_name)
        r = db.view(
            view_name,
            key=barcode,
            include_docs=True,
        )
        for row in r:
            firstdoc = row['doc']
        return firstdoc

    def _open_mdt(self, mdt_name, db_name='mdtcouch_test'):
        """Opens reads and returns an instance of MDT in CouchDB"""
        mdt = {}
        server = Server()
        db = server.get_or_create_db(db_name)
        r = db.view(
            '_all_docs',
            key=mdt_name,
            include_docs=True,
        )
        for row in r:
            mdt = row['doc']
        return mdt

    def _check_search_results_order(self, response):
        """Checks MUI search results page against regexp to determine document names order in a page"""
        prog = re.compile("""/mdtui/view/(?P<code>[A-Z]{3}-[0-9]{4})""", re.DOTALL)
        matches = prog.findall(str(response))
        return matches

    def _check_sorting_order_results(self, results_url, sort_query, result):
        """Helper for test (search_results_sorting) to reduce redundancy in check results"""
        response = self.client.post(results_url, sort_query)
        code_order = self._check_search_results_order(response)
        self.assertEqual(code_order, result)

    def _api_upload_file(self, doc, suggested_format='pdf', hash_code=None, check_response=True, update=False):
        ok_code = 200
        # Do file upload using DMS API
        file_path = os.path.join(self.test_document_files_dir, doc + '.' + suggested_format)
        data = {'file': open(file_path, 'r')}
        url = reverse('api_file', kwargs={'code': doc, 'suggested_format': suggested_format, })
        if hash_code:
            # Add hash to payload
            data['h'] = hash_code
        if not update:
            response = self.client.post(url, data)
            ok_code = 201
        else:
            response = self.client.put(url, data)
        if check_response:
            self.assertEqual(response.status_code, ok_code)
        return response

    def _shelve(self, obj, name='1.html'):
        """Writes given object into a file on desktop. (For debug purposes only ;) """
        fo = False
        path = os.path.expanduser(os.path.join('~', 'Desktop', name))
        # Cleaning existing file
        try:
            with open(path):
                os.remove(path)
                pass
        except IOError:
            pass
        # Dumping object into file
        try:
            fo = open(path, 'w')
        except Exception, e:
            print e
            pass
        if fo:
            fo.writelines(obj)
            print 'file %s written' % name


class PaginatorTestCase(TestCase):
    """Tests Paginator functionality and logic"""

    def test_paginator_tag_logic(self):
        """Refs #805: Testing Paginator tag logic

        Testing proper rendering of Digg like paginator
        """
        sequence = [str(i) for i in range(200)]
        paginated = Paginator(sequence, 10)
        result_sequence = rebuild_sequence_digg(paginated.page(1))
        self.assertEqual(result_sequence, [1, 2, '...', 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(2))
        self.assertEqual(result_sequence, [1, 2, 3, '...', 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(3))
        self.assertEqual(result_sequence, [1, 2, 3, 4, '...', 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(4))
        self.assertEqual(result_sequence, [1, 2, 3, 4, 5, '...', 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(5))
        self.assertEqual(result_sequence, [1, 2, '...', 4, 5, 6, '...', 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(17))
        self.assertEqual(result_sequence, [1, 2, '...', 16, 17, 18, 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(18))
        self.assertEqual(result_sequence, [1, 2, '...',  17, 18, 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(19))
        self.assertEqual(result_sequence, [1, 2, '...', 18, 19, 20])
        result_sequence = rebuild_sequence_digg(paginated.page(20))
        self.assertEqual(result_sequence, [1, 2, '...', 19, 20])


class MDTUI(MUITestData):
    """Tests for MUI interface of DMS"""

    def setUp(self):
        """Initialisation that happens for each test"""
        # We are using only logged in client in this test
        self.client.login(username=self.username, password=self.password)
        self.response = None

    def test_01_setup_mdts(self):
        """
        Setup all MDTs for the test suite.
        Made it standalone test because we need it to be run only once
        """
        # adding our MDT's required through API. (MDT API should be working)
        url = reverse('api_mdt')
        # List formatted so to comment out any MDT easily
        for m in [
            self.mdt1,
            self.mdt2,
            self.mdt3,
            self.mdt4,
            self.mdt5,
            self.mdt6,
            self.mdt7,
            self.mdt8,
        ]:
            mdt = json.dumps(m)
            response = self.client.post(url, {"mdt": mdt})
            if not response.status_code == 409:
                self.assertEqual(response.status_code, 200)
            else:
                raise AssertionError('MDT %s exists!' % m['_id'])

    def test_02_posting_document_with_all_keys(self):
        """
        Uploading File though MDTUI, adding all Secondary indexes accordingly.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc1_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertContains(response, 'Friends ID: 123')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        f_name = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', self.doc1+'.pdf')
        data = {'file': open(f_name, 'rb'), 'uploaded': u''}
        response = self.client.post(url+'?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, self.indexing_done_string)
        self.assertContains(response, 'Friends Name: Andrew')
        self.assertContains(response, 'Start Again')

    def test_03_additional_docs_adding(self):
        """Changes doc1 to new one for consistency.
        Adds additional document 2 and 3 for more complex tests.
        Those docs must be used farther for complex searches."""
        # Delete file "doc1" to cleanup after old tests
        url = reverse('api_file', kwargs={'code': self.doc1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        # POSTING DOCUMENT 2
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc1_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        self.assertContains(response, 'Friends ID: 123')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        f_name = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', self.doc1 + '.pdf')
        data = {'file': open(f_name, 'rb'), 'uploaded': u''}
        response = self.client.post(uurl + '?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, self.indexing_done_string)
        self.assertContains(response, 'Friends Name: Andrew')
        self.assertContains(response, 'Start Again')

        # POSTING DOCUMENT 1
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc2_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        self.assertContains(response, 'Friends ID: 321')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        f = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', self.doc2 + '.pdf')
        data = {'file': open(f, 'rb'), 'uploaded': u''}
        response = self.client.post(uurl + '?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, self.indexing_done_string)
        self.assertContains(response, 'Friends Name: Yuri')
        self.assertContains(response, 'Start Again')

        # POSTING DOCUMENT 3
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc3_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        uurl = self._retrieve_redirect_response_url(response)
        response = self.client.get(uurl)
        self.assertContains(response, 'Friends ID: 222')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        f = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', 'ADL-1111.pdf')
        data = {'file': open(f, 'rb'), 'uploaded': u''}
        response = self.client.post(uurl+'?uploaded', data)
        # Follow Redirect
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, self.indexing_done_string)
        self.assertContains(response, 'Friends Name: Someone')
        self.assertContains(response, 'Start Again')

    def test_04_additional_docs_adding_another_docrule(self):
        """
        Adds additional documents 1 and 2 for more complex tests
        with other docrule and another MDT.
        Those docs must be used farther for complex searches and testing JTG behavioural requirements.
        """
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict, self.m2_doc3_dict]:
            # Selecting Document Type Rule
            url = reverse('mdtui-index-type')
            response = self.client.post(url, {self.test_mdt_docrule_id2: 'docrule'})
            self.assertEqual(response.status_code, 302)
            # Getting indexes form and matching form Indexing Form fields names
            url = reverse('mdtui-index-details')
            response = self.client.get(url)
            rows_dict = self._read_indexes_form(response)
            post_dict = self._convert_doc_to_post_dict(rows_dict, doc_dict)
            # Adding Document Indexes
            response = self.client.post(url, post_dict)
            self.assertEqual(response.status_code, 302)
            uurl = self._retrieve_redirect_response_url(response)
            response = self.client.get(uurl)
            # Keys added to indexes
            self.assertContains(response, 'Reporting Entity: '+doc_dict['Reporting Entity'])
            self.assertEqual(response.status_code, 200)
            # Make the file upload
            f = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', self.doc1+'.pdf')
            data = {'file': open(f, 'rb'), 'uploaded': u''}
            response = self.client.post(uurl+'?uploaded', data)
            # Follow Redirect
            self.assertEqual(response.status_code, 302)
            new_url = self._retrieve_redirect_response_url(response)
            response = self.client.get(new_url)
            self.assertContains(response, self.indexing_done_string)
            self.assertContains(response, 'Report Date: '+doc_dict['Report Date'])
            self.assertContains(response, 'Start Again')

    def test_05_additional_docs_adding_third_docrule(self):
        """
        Adds additional documents 1 and 2 for more complex tests
        with Document Type 3 and another MDTs.
        Those docs must be used farther for complex searches and testing JTG behavioural requirements.
        """
        for doc_dict in [self.m5_doc1_dict, self.m5_doc2_dict]:
            # Selecting Document Type Rule
            url = reverse('mdtui-index-type')
            response = self.client.post(url, {self.test_mdt_docrule_id3: 'docrule'})
            self.assertEqual(response.status_code, 302)
            # Getting indexes form and matching form Indexing Form fields names
            url = reverse('mdtui-index-details')
            response = self.client.get(url)
            rows_dict = self._read_indexes_form(response)
            post_dict = self._convert_doc_to_post_dict(rows_dict, doc_dict)
            # Adding Document Indexes
            response = self.client.post(url, post_dict)
            self.assertEqual(response.status_code, 302)
            uurl = self._retrieve_redirect_response_url(response)
            response = self.client.get(uurl)
            # Keys added to indexes
            self.assertContains(response, 'Description: Test Document Number')
            self.assertEqual(response.status_code, 200)
            # Make the file upload
            f = os.path.join(settings.FIXTURE_DIRS[0], 'testdata', self.doc1 + '.pdf')
            data = {'file': open(f, 'rb'), 'uploaded': u''}
            response = self.client.post(uurl+'?uploaded', data)
            # Follow Redirect
            self.assertEqual(response.status_code, 302)
            new_url = self._retrieve_redirect_response_url(response)
            response = self.client.get(new_url)
            self.assertContains(response, self.indexing_done_string)
            self.assertContains(response, 'Employee: ' + doc_dict['Employee'])
            self.assertContains(response, 'Start Again')

    def test_06_opens_app(self):
        """
        If MDTUI app opens normally at least
        """
        url = reverse('mdtui-home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'To continue, choose from the options below')
        # Version rendered (#757)v
        self.assertContains(response, 'Version:')
        self.assertContains(response, 'Logged in as')

    def test_07_step1(self):
        """
        MDTUI Indexing has step 1 rendered properly.
        """
        url = reverse('mdtui-index-type')
        response = self.client.get(url)
        self.assertContains(response, '<legend>Step 1: Select Document Type</legend>')
        self.assertContains(response, 'Adlibre Invoices')
        self.assertEqual(response.status_code, 200)

    def test_08_step1_post_redirect(self):
        """
        MDTUI Displays Step 2 Properly (after proper call)
        """
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label class="control-label">Description</label>')
        self.assertContains(response, 'Creation Date')

    def test_09_indexing_step2_proper_form_rendering(self):
        """
        MDTUI renders Indexing form according to MDT's exist for testsuite's Docrule
        Step 2. Indexing Form contains MDT fields required.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
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

    def test_10_adding_indexes(self):
        """
        MDTUI Indexing Form parses data properly.
        Step 3 Displays appropriate indexes fro document will be uploaded.
        Posting to Indexing Step 3 returns proper data.
        """
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-index-details")
        # Getting indexes form and matching form Indexing Form fields names
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc1_dict)
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
        # Contains ability to print barcode or upload file
        # Bug #792 MUI: Barcode/Upload document without indexes bug.
        self.assertContains(response, '<a href="#fileModal')
        self.assertContains(response, '<a href="#printModal')

    def test_11_rendering_form_without_first_step(self):
        """Indexing Page 3 without populating previous forms contains proper warnings."""
        url = reverse("mdtui-index-source")
        response = self.client.get(url)
        self.assertContains(response, "You have not entered Document Indexing Data.")

    def test_12_metadata_exists_for_uploaded_documents(self):
        """Document now exists in couchDB
        Querying CouchDB itself to test docs exist."""
        url = self.couchdb_url + '/' + self.couchdb_name + '/' + self.doc1 + '?revs_info=true'
        # HACK: faking 'request' object here
        r = self.client.get(url)
        cou = urllib.urlopen(url)
        resp = cou.read()
        r.status_code = 200
        r.content = resp
        self.assertContains(r, self.doc1)
        self.assertContains(r, 'Iurii Garmash')

    def test_13_search_works(self):
        """Testing Search part opens."""
        url = reverse('mdtui-search')
        response = self.client.get(url)
        self.assertContains(response, 'mdt5')
        self.assertContains(response, 'Document Search')
        self.assertEqual(response.status_code, 200)

    def test_14_search_indexes_warning(self):
        """Testing Search part Warning for indexes."""
        url = reverse('mdtui-search-options')
        response = self.client.get(url)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_MDTS'])
        self.assertEqual(response.status_code, 200)

    def test_15_search_results_warning(self):
        """Testing Search part  warning for results."""
        url = reverse('mdtui-search-results')
        response = self.client.get(url)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        self.assertEqual(response.status_code, 200)

    def test_16_search_docrule_select_improper_call(self):
        """Makes wrong request to view. Response returns back to docrule selection."""
        url = reverse('mdtui-search-type')
        response = self.client.post(url)
        self.assertContains(response, 'mdt5')
        self.assertEqual(response.status_code, 200)

    def test_17_search_MDT_selection(self):
        """
        Proper Searching call.
        """
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # checking for proper fields rendering
        self.assertContains(response, "Creation Date From")
        self.assertContains(response, "Creation Date To")
        self.assertContains(response, "Employee")
        self.assertNotContains(response, "Description</label>")
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['NO_MDTS'])
        self.assertEqual(response.status_code, 200)

    def test_18_search_mdt_date_only_proper(self):
        """
        Proper call to search by date.
        MDTUI Search By Indexes Form parses data properly.
        Search Step 3 displays proper captured indexes.
        """
        search_MDT_date_range_1 = {
            u'date': self.doc1_dict["date"],
            u'end_date': u'',
            u'0': u'',
        }
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1 Indexes
        response = self.client.post(url, search_MDT_date_range_1)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # no errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # documents found
        self.assertContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_3)
        self.assertContains(response, self.edit_document_name_5)
        self.assertContains(response, self.edit_document_name_1)
        self.assertContains(response, self.edit_document_name_4)
        self.assertContains(response, self.m2_doc1_dict['description'])
        # context processors provide Document Type names
        self.assertContains(response, "Test doc type 3")
        self.assertContains(response, "Test doc type 3")
        # Contains only apropriate content types
        self.assertNotContains(response, "Adlibre invoices")

    def test_19_search_docrule_by_key_proper(self):
        """
        Proper call to search by secondary index key.
        Search Step 3 displays proper captured indexes.
        """
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # assigning form fields
        url = reverse('mdtui-search-options')
        response = self.client.get(url)
        # Getting indexes form and matching form Indexing Form fields names
        rows_dict = self._read_indexes_form(response)
        search_dict = self._create_search_dict_range_and_keys_for_search(self.doc1_dict, rows_dict)
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
        self.assertContains(response, self.doc1)
        # context processors provide docrule name
        self.assertContains(response, "Adlibre invoices")

    def test_20_search_by_date_improper(self):
        """Improper call to search by date.
        Search Step 3 does not display doc1."""
        # using today's date to avoid doc exists.
        date_req = datetime.datetime.now()
        date_str = datetime.datetime.strftime(date_req, settings.DATE_FORMAT)
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1 Indexes
        response = self.client.post(url, {'date': date_str, '0': ''})
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # no errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # document not found
        self.assertNotContains(response, self.edit_document_name_3)
        self.assertNotContains(response, self.edit_document_name_5)
        self.assertNotContains(response, self.edit_document_name_1)
        self.assertNotContains(response, self.edit_document_name_4)

    def test_21_add_indexes_unvalidated_form_preserves_prepopulated_data(self):
        """MDTUI Indexing Form .
        Step 2 adding indexes into several fields instead of all required
        returns prepopulated form with errors."""
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-index-details")
        # Getting indexes form and matching form Indexing Form fields names
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc1_dict)
        # Modifying post to brake it
        post_dict["description"] = u''
        post_dict["0"] = u''
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 200)
        # Response contains proper validation data
        self.assertContains(response, 'Brief Document Description')  # form fields help exists
        self.assertContains(response, 'Name of tests person')
        self.assertContains(response, date_standardized('2012-03-06'))  # docs data populated into form
        self.assertContains(response, 'Andrew')
        self.assertContains(response, '123456')
        self.assertContains(response, 'Iurii Garmash')
        # autocomplete (typehead) scripts rendered
        self.assertContains(response, """connect_typeahead("#id_0", "Friends ID", '/mdtui/parallel/');""")
        self.assertContains(response, """connect_typeahead("#id_1", "Friends Name", '/mdtui/parallel/');""")
        self.assertContains(response, 'This field is required')  # form renders errors

    def test_22_parallel_keys_indexing_proper(self):
        """Testing Parallel keys lookup for recently uploaded document"""
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, self.typehead_call1)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>')  # json but not html response
        self.assertContains(response, 'Friends ID')  # Proper keys
        self.assertContains(response, '123')
        self.assertContains(response, 'Friends Name')
        self.assertContains(response, 'Andrew')
        self.assertNotContains(response, 'Iurii Garmash')  # Improper key
        self.assertNotContains(response, 'Employee Name')
        self.assertNotContains(response, 'Required Date')

    def test_23_parallel_keys_indexing_wrong(self):
        """Testing Parallel keys lookup for recently uploaded document"""
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, self.typehead_call3)
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

    def test_24_parallel_keys_indexing_set2_proper(self):
        """Testing Parallel keys lookup for recently uploaded document."""
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, self.typehead_call2)
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

    def test_25_parallel_keys_search_proper(self):
        """Testing Parallel keys lookup for recently uploaded document"""
        # Selecting MDT
        url = reverse('mdtui-search-type')
        response = self.client.post(url, {'docrule': self.test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        # Adding Document Indexes
        response = self.client.post(url, self.typehead_call1)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>')  # json but not html response
        self.assertContains(response, 'Friends ID')  # Proper keys
        self.assertContains(response, '123')
        self.assertContains(response, 'Friends Name')
        self.assertContains(response, 'Andrew')
        self.assertNotContains(response, 'Iurii Garmash')  # Improper key
        self.assertNotContains(response, 'Employee Name')

    def test_26_parallel_keys_searching_set2_proper(self):
        """Testing Parallel keys lookup for recently uploaded document"""
        # Selecting Document Type Rule
        url = reverse('mdtui-search-type')
        response = self.client.post(url, {'docrule': self.test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, self.typehead_call2)
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

    def test_27_parallel_keys_indexing_wrong(self):
        """Testing Parallel keys lookup for recently uploaded document"""
        # Selecting Document Type Rule
        url = reverse('mdtui-search-type')
        response = self.client.post(url, {'docrule': self.test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, self.typehead_call3)
        self.assertEqual(response.status_code, 200)
        # Response contains proper data
        self.assertNotContains(response, '<html>')
        self.assertNotContains(response, 'Friends ID')
        self.assertNotContains(response, '123')
        self.assertNotContains(response, 'Friends Name')
        self.assertNotContains(response, 'Andrew')
        self.assertNotContains(response, 'Iurii Garmash')
        self.assertNotContains(response, 'Employee Name')

    def test_28_search_by_date_range_only_proper_all_3_docs(self):
        """Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays all 3 docs for given date range. (Proper)
        All docs render their indexes correctly.
        Names autogenarated for docs. e.g. ADL-0001, ADL-0002, ADL-0003
        (Not ADL-0001, ADL-0002, ADL-1111 like files uploaded)"""
        all3_docs_range = {
            u'end_date': unicode(date_standardized('2012-03-30')),
            u'1': u'',
            u'0': u'',
            u'3': u'',
            u'2': u'',
            u'4': u'',
            u'date': unicode(date_standardized('2012-03-01')),
        }
        # setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
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
        self.assertContains(response, self.doc1)
        self.assertContains(response, self.doc1_dict['description'])
        self.assertContains(response, self.doc2)
        self.assertContains(response, self.doc2_dict['description'])
        self.assertContains(response, self.doc3)
        self.assertContains(response, self.doc3_dict['description'])
        # Context processors provide docrule name
        self.assertContains(response, "Adlibre invoices")
        # 3 documents secondary keys present
        for doc in [self.doc1_dict, self.doc2_dict, self.doc3_dict]:
            for key in doc.iterkeys():
                if key != 'date' and key != 'description':
                    # Secondary key to test
                    self.assertContains(response, doc[key])
        # Searching keys exist in search results
        self.assertContains(response, date_standardized('2012-03-30'))
        self.assertContains(response, date_standardized('2012-03-01'))
        # docs for mdt3 does not present in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_29_search_by_date_range_only_proper_2_docs_without_1(self):
        """Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays all 2 docs for given date range. (Proper)
        And does not contain doc3 values.
        All docs render their indexes correctly."""
        # setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = self.date_range_1and2_not3
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # 3 documents found
        self.assertContains(response, self.doc1)
        self.assertContains(response, self.doc1_dict['description'])
        self.assertContains(response, self.doc2)
        self.assertContains(response, self.doc2_dict['description'])
        # Context processors provide docrule name
        self.assertContains(response, "Adlibre invoices")
        # 2 documents secondary keys present
        for doc in [self.doc1_dict, self.doc2_dict]:
            for key in doc.iterkeys():
                if key != 'date' and not key != 'description':
                    # Secondary key to test
                    self.assertContains(response, doc[key])
        # No unique doc3 keys exist
        self.assertNotContains(response, self.doc3)
        self.assertNotContains(response, self.doc3_dict['description'])
        self.assertNotContains(response, self.doc3_dict['Required Date'])
        self.assertNotContains(response, self.doc3_dict['Friends ID'])
        self.assertNotContains(response, self.doc3_dict['Friends Name'])
        # Searching keys exist in search results
        self.assertContains(response, date_standardized('2012-03-20'))
        self.assertContains(response, date_standardized('2012-03-01'))
        # docs for mdt3 does not present in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_30_search_by_date_range_only_proper_3_d_doc_only(self):
        """
        Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc3 only for given date range. (Proper)
        And does not contain doc1 and2 unique values.
        All docs render their indexes correctly.
        """
        date_range_only3 = {
            u'end_date': unicode(date_standardized('2012-03-30')),
            u'1': u'',
            u'0': u'',
            u'3': u'',
            u'2': u'',
            u'4': u'',
            u'date': unicode(date_standardized('2012-03-25')),
        }
        # setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
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
        self.assertNotContains(response, self.doc1)
        self.assertNotContains(response, self.doc2)
        # Context processors provide docrule name
        self.assertContains(response, "Adlibre invoices")
        # 2 first documents secondary keys NOT present
        for doc in [self.doc1_dict, self.doc2_dict]:
            for key in doc.iterkeys():
                if not key in ['Employee Name', 'Friends Name', 'Employee ID']:  # Collision with docs 1 and 2
                    # Secondary key to test
                    self.assertNotContains(response, doc[key])
        # Full doc3 data exist
        self.assertContains(response, self.doc3)
        for key in self.doc3_dict.iterkeys():
            # Secondary key to test
            self.assertContains(response, self.doc3_dict[key])
        # Searching keys exist in search results
        self.assertContains(response, date_standardized('2012-03-30'))
        self.assertContains(response, date_standardized('2012-03-25'))
        # docs for mdt3 does not present in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_31_search_by_date_range_no_docs(self):
        """
        Proper call to search by date range only.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc3 only for given date range. (Proper)
        And does not contain doc1 and2 unique values.
        All docs render their indexes correctly.
        """
        # Setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = self.date_range_none
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # none of 3 documents present in response
        self.assertNotContains(response, self.doc1)
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc3)
        # Searching keys exist in search results
        self.assertContains(response, date_standardized('2012-03-30'))
        self.assertContains(response, date_standardized('2012-03-31'))
        # docs for mdt3 does not present in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_32_search_by_date_range_with_keys_1(self):
        """Proper call to search by date range with integer and string keys.
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc1 only for given date range and doc1 unique keys. (Proper)
        And does not contain doc2 and3 unique values.
        All docs render their indexes correctly"""
        date_range_with_keys_doc1 = {
            u'Friends ID': u'123',
            u'Friends Name': u'Andrew',
        }
        # Setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        data = self._create_search_dict_for_range_and_keys(
            date_range_with_keys_doc1,
            ids,
            self.date_range_with_keys_3_docs,
        )
        # Searching date range with unique doc1 keys
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # none of 2 other documents present in response
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc3)
        # Searching keys exist in search results
        self.assertContains(response, self.date_range_with_keys_3_docs[u'date'])
        self.assertContains(response, self.date_range_with_keys_3_docs[u'end_date'])
        for key, value in date_range_with_keys_doc1.iteritems():
            self.assertContains(response, value)
        # doc1 data exist in response
        for key, value in self.doc1_dict.iteritems():
            self.assertContains(response, value)
        # docs for mdt3 does not present in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_33_search_by_date_range_with_keys_2(self):
        """
        Proper call to search by date range with one key for 2 docs (2 and 3).
        MDTUI Search By Index Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc2 and doc3 for given date range and key. (Proper)
        And does not contain doc1 unique values.
        All docs render their indexes correctly.
        """
        date_range_with_keys_doc2 = {
            u'Friends Name': u'Yuri',
        }
        # Setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        data = self._create_search_dict_for_range_and_keys(
            date_range_with_keys_doc2,
            ids,
            self.date_range_with_keys_3_docs,
        )
        # Searching date range with unique doc1 keys
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # No doc1 document present in response
        self.assertNotContains(response, self.doc1)
        # Searching keys exist in search results
        self.assertContains(response, self.date_range_with_keys_3_docs[u'date'])
        self.assertContains(response, self.date_range_with_keys_3_docs[u'end_date'])
        for key, value in date_range_with_keys_doc2.iteritems():
            self.assertContains(response, value)
        # doc2 and doc3 data exist in response
        for doc_dict in [self.doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertContains(response, value)
        # Does not contain doc1 unique values
        self.assertNotContains(response, self.doc1_dict['description'])
        self.assertNotContains(response, self.doc1_dict['Employee Name'])  # Iurii Garmash
        # docs for mdt3 does not present in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_34_search_date_range_withing_2_different_docrules(self):
        """MUI search collisions bugs absent.
        Search by date range returns result for docs only from this MDT.
        Search Step 'results' displays proper captured indexes for docrule2 of those tests.
        (MDT3) keys are displayed and MDT's 1 and 2 does not displaying.
        2 test docs for MDT3 rendered"""
        # Setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id2}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, self.all_docs_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Searching keys exist in search results
        self.assertContains(response, self.all_docs_range[u'date'])
        self.assertContains(response, self.all_docs_range[u'end_date'])
        # doc1 and doc2 for MDT3 data exist in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertContains(response, value)
        # Test doc's filenames generated properly
        self.assertContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_3)
        # Does not contain unique values from docs in another docrules
        for doc_dict in [self.doc1_dict, self.doc2_dict, self.doc3_dict]:
            self.assertNotContains(response, doc_dict['description'])
            self.assertNotContains(response, doc_dict['Employee Name'])
        # Keys from MDT-s 1 and 2 not rendered vin search response
        for key in self.doc1_dict.iterkeys():
            if key != 'date' and key != 'description' and key != 'Additional':
                self.assertNotContains(response, key)

    def test_35_search_date_range_withing_2_different_docrules_2(self):
        """MUI search collisions bugs absent.
        Search by date range returns result for docs only from this docrule.
        Search Step 'results' displays proper captured indexes for docrule1 of those tests.
        (MDT1 and MDT2) keys are displayed and MDT3 keys does not displaying.
        3 test docs for MDT1 and MDT2 rendered"""
        # Setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, self.all_docs_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Searching keys exist in search results
        self.assertContains(response, self.all_docs_range[u'date'])
        self.assertContains(response, self.all_docs_range[u'end_date'])
        # doc1, doc2 for MDTs 2 and 3 data exist in response
        for doc_dict in [self.m5_doc1_dict, self.m5_doc2_dict, self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                # Uppercase value hack
                if value == 'some data' or value == 'some other data':
                    value = value.upper()
                self.assertContains(response, value)
        # Test doc's file-names generated properly
        self.assertContains(response, self.edit_document_name_1)
        self.assertContains(response, self.edit_document_name_4)
        self.assertContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_3)
        # Does not contain another docs
        self.assertNotContains(response, self.doc1)
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc3)

    def test_36_search_date_range_withing_2_different_docrules_with_keys(self):
        """
        MUI search collisions bugs absent.
        Search by date range returns result for docs only from this docrule.
        Search Step 'results' displays proper captured indexes for docrule2 of those tests.
        (MDT3) keys are displayed and MDT's 1 and 2 does not displaying.
        2 test docs for MDT3 rendered.
        """
        all_docs_range_and_key = {
            u'date': unicode(date_standardized('2012-03-01')),
            u'end_date': unicode(date_standardized('2012-05-05')),
            u'0': u'Andrew',
        }
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
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
        for doc_dict in [self.m5_doc1_dict, self.m5_doc2_dict, self.m2_doc3_dict]:
            for key, value in doc_dict.iteritems():
                # Uppercase value hack
                if value == 'some data' or value == 'some other data':
                    value = value.upper()
                self.assertContains(response, value)
            # Test doc's filenames generated properly
        self.assertContains(response, self.edit_document_name_1)
        self.assertContains(response, self.edit_document_name_4)
        self.assertContains(response, self.edit_document_name_5)
        # Does not contain another docs
        self.assertNotContains(response, self.doc1)
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc3)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)
        # Not contains 2 document dict fields
        self.assertNotContains(response, 'metadata_user_name')
        self.assertNotContains(response, 'metadata_user_id')

    def test_37_uppercase_fields_lowercase_data(self):
        """
        Adds MDT indexes to test Uppercase fields behaviour.
        """
        upper_wrong_dict = {
            u'date': [unicode(date_standardized('2012-04-17'))],
            u'0': [u'lowercase data'],
            u'description': [u'something usefull']
        }
        # Lowercase field provided
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id3: 'docrule'})
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
        self.assertContains(response, self.indexes_added_string)

    def test_38_uppercase_fields_UPPERCASE_DATA(self):
        """" Normal uppercase field rendering and using """
        upper_right_dict = {
            u'date': [unicode(date_standardized('2012-04-17'))],
            u'0': [u'UPPERCASE DATA'],
            u'description': [u'something usefull']
        }
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id3: 'docrule'})
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
        self.assertContains(response, self.indexes_added_string)

    def test_39_search_by_keys_only_contains_secondary_date_range(self):
        """
        Proper call to search by secondary key date range key.
        MDTUI Search By Search Form parses data properly.
        Search Step 'results' displays proper captured indexes.
        Search displays full doc1 for given secondary key of 'date' type. (Proper)
        And does not contain doc2 and doc3 unique values.
        All docs render their indexes correctly.
        """
        date_type_key_doc1 = {
            u'Required Date': unicode(date_standardized('2012-03-07')),
        }
        # Setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        # Dict without actual date
        data = self._create_search_dict_range_and_keys_for_search(
            date_type_key_doc1,
            ids,
        )
        # Searching date range with unique doc1 keys
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # None of doc2 and doc3 present in response
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc3)
        self.assertNotContains(response, self.doc2_dict['description'])
        self.assertNotContains(response, self.doc3_dict['description'])
        # Searching keys exist in search results
        for key, value in date_type_key_doc1.iteritems():
            self.assertContains(response, value)
        # doc1 data exist in response
        for key, value in self.doc1_dict.iteritems():
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
        self.assertContains(response, self.doc1)
        # docs for mdt3 does not present in response
        for doc_dict in [self.m2_doc1_dict, self.m2_doc2_dict]:
            for key, value in doc_dict.iteritems():
                self.assertNotContains(response, value)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_40_autocomplete_single_key(self):
        """
        Testing Parallel keys lookup for recently uploaded document
        Single key must be returned.
        Must render suggestion for this key only.
        """
        typehead_call4 = {
            'key_name': 'Reporting Entity',
            'autocomplete_search': 'JTG'
        }
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id2: 'docrule'})
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
        typehead_call = {
            'key_name': 'Reporting Entity',
            'autocomplete_search': '111'
        }
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id2: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Reporting Entity')
        self.assertNotContains(response, 'JTG')

    def test_42_trim_whitespaces_works_on_all_fields(self):
        """
        All fields should trim whitespaces upon submitting indexes form
        """
        ind_doc1 = {
            'date': date_standardized('2012-04-03'),
            'description': 'Test Document MDT 3 Number 2                                 ',
            'Reporting Entity': 'FCB                                            ',
            'Report Date': date_standardized('2012-04-04'),
            'Report Type': '                     Pay run                           ',
        }
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id2: 'docrule'})
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
        self.assertEqual(response.status_code, 200)
        # Keys added to indexes
        self.assertNotContains(response, 'Reporting Entity: '+ind_doc1['Reporting Entity'])
        self.assertContains(response, 'Reporting Entity: '+ind_doc1['Reporting Entity'].strip(' \t\n\r'))

    def test_43_date_keys_converted_to_date_ranges_on_search(self):
        """Date keys provided converted to date ranges with start/end date period
        for both document indexing date/secondary dates key types."""
        range_gen1 = {
            'end_date': date_standardized('2012-04-02'),
            'Report Date From': date_standardized('2012-03-30')
        }
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id2}
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
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc3)
        self.assertNotContains(response, self.doc2_dict['description'])
        self.assertNotContains(response, self.doc3_dict['description'])
        # Things that should be here
        self.assertContains(response, date_standardized('2100-01-01'))  # Max date range
        self.assertContains(response, date_standardized('1960-01-01'))  # Min date range
        self.assertContains(response, date_standardized('2012-04-02'))
        report_string = 'Report Date: (from: %s to: %s)' % (
            date_standardized('2012-03-30'),
            date_standardized('2100-01-01')
        )
        self.assertContains(response, report_string)  # Range recognised properly
        self.assertContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_3)
        self.assertContains(response, self.edit_document_name_5)

    def test_44_warns_about_new_parallel_key(self):
        """
        Warns about new parallel keys created
        """
        doc1_creates_warnigs_string = 'Adding new indexing key: Employee ID: 1234567'
        doc1_creates_warnigs_dict = {
            'date': date_standardized('2012-03-06'),
            'description': 'Test Document Number N',
            'Employee ID': '1234567',
            'Required Date': date_standardized('2012-03-07'),
            'Employee Name': 'Iurii Garmash',
            'Friends ID': '123',
            'Friends Name': 'Andrew',
        }
        # Selecting DocumentTypeRule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
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
        # Requests search of BBB-0001 document only specifying date range for it
        date_range_withing_2_ranges_1 = {
            u'2_to': [u'02/04/2012'],
            u'end_date': [u'05/04/2012'],
            u'2_from': [u'01/04/2012'],
            u'1': [u''],
            u'0': [u''],
            u'3': [u''],
            u'date': [u'01/04/2012'],
        }
        # setting docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id2}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        self.client.get(url)
        # Searching date range with unique doc1 keys
        response = self.client.post(url, date_range_withing_2_ranges_1)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and only one doc persists there
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.edit_document_name_2)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # None of doc2 of this docrule and docs from other docrules exist in response
        self.assertNotContains(response, self.doc1)
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc3)
        self.assertNotContains(response, self.edit_document_name_3)

    def test_46_security_restricts_search_or_index(self):
        """Groups for accessing search or index sections of MUI """
        # We need another logged in user for this test
        self.client.logout()
        self.client.login(username=self.username_1, password=self.password_1)
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
        self.client.login(username=self.username_2, password=self.password_2)
        # User test2 have access to index
        response = self.client.get(index_url)
        self.assertEqual(response.status_code, 200)
        # User test2 do not have access to search
        response = self.client.get(search_url)
        self.assertNotEqual(response.status_code, 200)
        self.client.logout()

    def test_47_indexing_mdt_choices_limited_by_permitted_docrules(self):
        """Permission are disabling document type rule choices for normal user in INDEX of MUI"""
        # We need another logged in user for this test
        self.client.logout()
        self.client.login(username=self.username_1, password=self.password_1)
        # Checking if user sees his own permitted document type rules
        url = reverse('mdtui-search-type')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mdt5')
        self.assertContains(response, 'mdt6')
        # And does not see hidden ones
        self.assertNotContains(response, 'mdt1')
        self.assertNotContains(response, 'mdt2')
        self.assertNotContains(response, 'mdt3')
        self.assertNotContains(response, 'mdt4')
        self.client.logout()

    def test_48_searching_docrule_choices_limited_by_permission(self):
        """Permission are disabling document type rule choices for normal user in SEARCH of MUI"""
        # We need another logged in user for this test
        self.client.logout()
        self.client.login(username=self.username_2, password=self.password_2)
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
        """Superuser sees all the document type rules"""
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
        self.assertContains(response, 'mdt5')
        self.assertContains(response, 'mdt6')

    def test_50_search_works_docrule(self):
        """Testing Search part renders Docrules"""
        url = reverse('mdtui-search')
        response = self.client.get(url)
        self.assertContains(response, 'Test Doc Type 2')
        self.assertContains(response, 'Test Doc Type 3')
        self.assertContains(response, 'Adlibre Invoices')
        self.assertContains(response, 'Test PDFs')
        self.assertContains(response, 'Document Search')
        self.assertContains(response, 'Document Type')
        self.assertContains(response, 'Custom Search')
        self.assertEqual(response.status_code, 200)

    def test_51_search_selecting_type_forms(self):
        """Testing search selection (step type) rendered correctly"""
        url = reverse('mdtui-search')
        # Selecting MDT
        response = self.client.post(url, self.select_mdt5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # Checking form rendered correctly
        self.assertContains(response, 'Search Options')
        self.assertContains(response, 'Employee')
        self.assertNotContains(response, 'Tests Uppercase Field')
        self.assertNotContains(response, 'Reporting Entity')
        # Going back to step type renders proper selection of MDT
        response = self.client.get(url)
        self.assertContains(response, '<option value="5" selected="selected">mdt5')
        # Selecting Document Type now
        response = self.client.post(url, self.select_docrule_7)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Options')
        self.assertContains(response, 'Reporting Entity')
        self.assertContains(response, 'Employee')
        self.assertContains(response, 'Report Date From')
        self.assertContains(response, 'Report Type')
        self.assertNotContains(response, 'Tests Uppercase Field')
        # Checking step Type selection:
        response = self.client.get(url)
        self.assertContains(response, '<option value="7" selected="selected">Test Doc Type 2')
        self.assertNotContains(response, '<option value="5" selected="selected">mdt5')

    def test_52_search_by_docrule_using_date_range_only(self):
        """
        Search by Document Type with date range only.
        """
        search_date_range_only_docrule_7_1 = {
            u'2_to': [u''],
            u'end_date': [u''],
            u'2_from': [u''],
            u'1': [u''],
            u'0': [u''],
            u'3': [u''],
            u'date': [u'01/03/2012'],
        }
        search_date_range_only_docrule_7_2 = {
            u'2_to': [u''],
            u'end_date': [u''],
            u'2_from': [u''],
            u'1': [u''],
            u'0': [u''],
            u'3': [u''],
            u'date': [u'30/04/2012'],
        }
        url = reverse('mdtui-search')
        # Selecting MDT
        response = self.client.post(url, self.select_docrule_7)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporting Entity')
        # Posting date range 1
        response = self.client.post(new_url, search_date_range_only_docrule_7_1)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_3)
        self.assertContains(response, self.edit_document_name_5)
        # Posting date range 2
        response = self.client.post(new_url, search_date_range_only_docrule_7_2)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)
        self.assertContains(response, self.edit_document_name_5)

    def test_53_search_by_docrule_using_date_range_and_keys(self):
        """
        Search complex queries that find documents by date ranges and/or combination of keys
        Checks:
        - 2 different date ranges,
        - 2 keys,
        - creation date range
        """
        search_date_range_and_keys_docrule_7_1 = {
            u'2_to': [u'10/07/2012'],
            u'end_date': [u''],
            u'2_from': [u'01/03/2012'],
            u'1': [u''],
            u'0': [u'JTG'],
            u'4': [u'Vovan'],
            u'date': [u'01/03/2012'],
        }
        search_date_range_and_keys_docrule_7_2 = {
            u'2_to': [u'30/04/2012'],
            u'end_date': [u''],
            u'2_from': [u'01/03/2012'],
            u'1': [u''],
            u'0': [u''],
            u'4': [u'Vovan'],
            u'date': [u'01/03/2012'],
        }
        url = reverse('mdtui-search')
        # Selecting MDT
        response = self.client.post(url, self.select_docrule_7)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporting Entity')
        # Posting params 1
        response = self.client.post(new_url, search_date_range_and_keys_docrule_7_1)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)
        self.assertNotContains(response, self.edit_document_name_5)
        # Posting params 2
        response = self.client.post(new_url, search_date_range_and_keys_docrule_7_2)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_3)
        self.assertNotContains(response, self.edit_document_name_5)

    def test_54_core_creation_indexes_left_the_same_on_update(self):
        """
        Testing Doc update sequence.
        e.g.:
        You have indexed document through MUI and printed a barcode.
        You now try to upload a document through API (e.g. from scanning house)
        Your document's User, Description and created date are left the same.
        """
        # Changing user
        self.client.logout()
        self.client.login(username=self.username_1, password=self.password_1)
        # Uploading file through browser app
        filename = settings.FIXTURE_DIRS[0] + '/testdata/' + self.doc1 + '.pdf'
        url = reverse('upload')
        data = {'file': open(filename, 'r'), }
        response = self.client.post(url, data)
        self.assertContains(response, 'File has been uploaded')
        # Faking 'request' object to test with assertions
        url = self.couchdb_url + '/' + self.couchdb_name + '/' + self.doc1 + '?revs_info=true'
        r = self.client.get(url)
        cou = urllib.urlopen(url)
        resp = cou.read()
        r.status_code = 200
        r.content = resp
        # Checking User/Description/Creation Date in new doc
        self.assertContains(r, self.doc1)  # Doc name present
        self.assertContains(r, self.doc1 + '_r2.pdf')  # Revision updated
        self.assertContains(r, 'Iurii Garmash')  # Indexes present
        self.assertContains(r, '"metadata_created_date":"2012-03-06T00:00:00Z"')  # creation date left as it is
        self.assertContains(r, '"metadata_user_name":"admin"')  # User left as is
        self.assertContains(r, '"metadata_user_id":"1"')  # User PK stored properly
        self.assertContains(r, self.doc1_dict['description'])  # Description preserved

    def test_55_mdt_empty_search(self):
        """
        Bug #791 MUI: Selecting MDT search results Exception.

        After selection of MDT and submitting "Search Options" form with empty results
        we have a bug that rises an exception in search results. Prevents from rendering.
        """
        search_MDT_5_empty_options_form = {
            u'date': u'',
            u'end_date': u'',
            u'0': u'',
        }
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        self.client.get(url)
        # Searching date range with unique doc1 keys
        response = self.client.post(url, search_MDT_5_empty_options_form)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and only one doc persists there
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        # No documents for any of docrules found in response
        self.assertNotContains(response, 'BBB-')
        self.assertNotContains(response, 'CCC-')
        self.assertNotContains(response, 'ADL-')

    def test_56_indexing_uploading_or_barcoding_without_indexes(self):
        """
        Bug #792 MUI: Barcode/Upload document without indexes bug.

        Bug that appears when user tries to upload or barcode document without:
        Submitting any indexes.
        Entering Document Type.
        (E.g. going into MDTUI and entering STEP 3 from scratch without filling any previous forms.)
        """
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        # Checking if response is ok to test this case
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_INDEX'])
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_DOCRULE'])
        # Printing Barcode or uploading modal showing disabled
        self.assertNotContains(response, '<a href="#fileModal')
        self.assertNotContains(response, '<a href="#printModal')

    def test_57_searching_by_MDT_filters_permitted_results(self):
        """
        Feature #716 Search by metadata template

        Need to make sure that searching using MDT
        will not go displaying protected documents in search results.

        Generally first test of restricted MDT's search results.
        """
        # Creating special user
        username_3 = 'tests_user_3'
        password_3 = 'test3'
        search_select_mdt_6 = {u'mdt': u'6'}
        search_seleect_mdt_6_date_range = {
            u'date': date_standardized('2012-01-01'),
            u'end_date': u'',
            u'0': u'',
        }
        user = User.objects.create_user(username_3, 'a@b.com', password_3)
        user.save()
        # Adding permission to interact Adlibre invoices only
        perm = Permission.objects.filter(name=u'Can interact Adlibre Invoices')
        user.user_permissions.add(perm[0])
        # Registering that user in required security groups and removing their permissions...
        for groupname in ['security', 'api', 'MUI Index interaction', 'MUI Search interaction']:
            g = Group.objects.get(name=groupname)
            g.user_set.add(user)
            for perm in g.permissions.all():
                g.permissions.remove(perm)
        # Logging in with this new user
        self.client.logout()
        self.client.login(username=username_3, password=password_3)
        url = reverse('mdtui-search-type')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, search_select_mdt_6)
        opt_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(opt_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(opt_url, search_seleect_mdt_6_date_range)
        res_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(res_url)
        # Checking if search result is filtered properly (Only 'Adlibre Invoices' Docuemnt Type's docs present)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.doc1)
        self.assertContains(response, self.doc2)
        self.assertContains(response, self.doc3)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertNotContains(response, self.edit_document_name_3)
        self.assertNotContains(response, self.edit_document_name_5)
        self.assertNotContains(response, self.edit_document_name_1)

        # Doing the same with adding second permission (for Test docrule 2)
        perm2 = Permission.objects.filter(name=u'Can interact Test Doc Type 2')
        user.user_permissions.add(perm2[0])
        # Reinitialising search:
        url = reverse('mdtui-search-type')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, search_select_mdt_6)
        opt_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(opt_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(opt_url, search_seleect_mdt_6_date_range)
        res_url = self._retrieve_redirect_response_url(response)
        self.client.get(res_url)
        response = self.client.get(res_url)
        # Checking if search result is filtered properly
        # ('Adlibre Invoices' and 'Test Doc Type 2' Docuemnt Type's docs present)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.doc1)
        self.assertContains(response, self.doc2)
        self.assertContains(response, self.doc3)
        self.assertContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_3)
        self.assertContains(response, self.edit_document_name_5)
        self.assertNotContains(response, self.edit_document_name_1)

    def test_58_user_sees_only_permitted_choices_MUI(self):
        """
        Feature  #755 MUI: Hide features user doesn't have access to

        Test #1 tests proper search rendering

        If a user doesn't have access to index or to search then those features
        (eg links / menu options) should be hidden.
        This will require some template modification, and some sort of context var to expose the permissions.
        """
        # Creating special user
        user = User.objects.create_user(self.username_4, 'b@c.com', self.password_4)
        user.save()
        # Adding permission to interact Adlibre invoices only
        perm = Permission.objects.filter(name=u'Can interact Adlibre Invoices')
        user.user_permissions.add(perm[0])
        # Registering that user in required security groups and removing their permissions...
        for groupname in ['security', 'MUI Search interaction']:
            g = Group.objects.get(name=groupname)
            g.user_set.add(user)
            for perm in g.permissions.all():
                g.permissions.remove(perm)

        # Using user 4 to check for search permissions and proper templates rendering
        self.client.logout()
        self.client.login(username=self.username_4, password=self.password_4)
        response = self.client.get(reverse('mdtui-home'))
        self.assertEqual(response.status_code, 200)
        # MUI search button rendered anywhere on the page
        self.assertContains(response, 'i class="icon-search icon-white">')
        # MUI NO index button icon rendered
        self.assertNotContains(response, 'i class="icon-barcode icon-white">')
        # MUI indexing big logo NOT rendered
        self.assertNotContains(response, 'barcode.png')
        # MUI Searching big logo rendered
        self.assertContains(response, 'search.png')

    def test_59_user_sees_only_permitted_choices_MUI(self):
        """
        Feature  #755 MUI: Hide features user doesn't have access to

        Test #2 Tests proper indexing rendering

        If a user doesn't have access to index or to search then those features
        (eg links / menu options) should be hidden.
        This will require some template modification, and some sort of context var to expose the permissions.
        """
        # test user 5
        username_5 = 'tests_user_5'
        password_5 = 'test5'
        # Creating special user
        user = User.objects.create_user(username_5, 'c@d.com', password_5)
        user.save()
        # Adding permission to interact Adlibre invoices only
        perm = Permission.objects.filter(name=u'Can interact Adlibre Invoices')
        user.user_permissions.add(perm[0])
        # Registering that user in required security groups and removing their permissions...
        for groupname in ['security', 'MUI Index interaction']:
            g = Group.objects.get(name=groupname)
            g.user_set.add(user)
            for perm in g.permissions.all():
                g.permissions.remove(perm)

        # Using user 5 to check for search permissions and proper templates rendering
        self.client.logout()
        self.client.login(username=username_5, password=password_5)
        response = self.client.get(reverse('mdtui-home'))
        self.assertEqual(response.status_code, 200)
        # MUI search button NOT rendered anywhere on the page
        self.assertNotContains(response, 'i class="icon-search icon-white">')
        # MUI index button icon rendered
        self.assertContains(response, 'i class="icon-barcode icon-white">')
        # MUI Searching big logo NOT rendered
        self.assertNotContains(response, 'search.png')
        # MUI Indexing big logo rendered
        self.assertContains(response, 'barcode.png')

    def test_60_autocomplete_single_key_no_duplicates(self):
        """
        Testing key lookup for single key

        Must render ONE suggestion for this key only.
        No duplicates in text should occur.
        """
        typehead_call = {
            'key_name': 'Employee',
            'autocomplete_search': 'And'
        }
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id2: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse("mdtui-parallel-keys")
        response = self.client.post(url, typehead_call)
        self.assertEqual(response.status_code, 200)
        # Checking response for duplicates
        self.assertContains(response, 'Employee')
        self.assertContains(response, 'Andrew')
        emp_count = re.findall('Employee', response.content)
        and_count = re.findall('Andrew', response.content)
        self.assertEqual(emp_count.__len__(), 1)
        self.assertEqual(and_count.__len__(), 1)

    def test_61_user_can_view_documents_from_permitted_docrules(self):
        """
        Testing user can view only documents that are allowed to him with user permissions.

        Testing MDTUI 'view document' view to redirect with permission limitations.
        In fact it's a test of API response through view and download pdf view proxies.
        Reflects issue #802
        """
        username_6 = 'tests_user_6'
        password_6 = 'test6'
        code1 = self.doc1
        code2 = self.edit_document_name_1
        # Creating special user
        user = User.objects.create_user(username_6, 'd@d.com', password_6)
        user.save()
        # Adding permission to interact Adlibre invoices only
        perm = Permission.objects.filter(name=u'Can interact Adlibre Invoices')
        user.user_permissions.add(perm[0])
        # Registering that user in required security groups and removing their permissions...
        for groupname in ['api', 'security', 'MUI Index interaction', 'MUI Search interaction']:
            g = Group.objects.get(name=groupname)
            g.user_set.add(user)
            for perm in g.permissions.all():
                g.permissions.remove(perm)
        # Logging in with this new user
        self.client.logout()
        self.client.login(username=username_6, password=password_6)
        # Checking accessibility
        url = reverse('mdtui-view-object', kwargs={'code': code1})
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 302)
        self.assertContains(response, code1)
        # Checking API directly
        url = reverse('api_file', kwargs={'code': code1, 'suggested_format': 'pdf'},)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '%PDF-1.4')  # PDF is there
        # Checking API directly (must not be there)
        url = reverse('api_file', kwargs={'code': code2, 'suggested_format': 'pdf'},)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)   # Forbidden code returned

    def test_62_mdt_empty_search(self):
        """
        Feature #801: MUI: Search Result Export moved from step 3 to step 2.

        Added additional button that returns export results rather than.
        Testing if it returns results in proper form. E.g. CSV file with all the data should be there.
        """
        search_MDT_5_export_results_test = {
            u'0': u'Andrew',
            u'date': u'',
            u'end_date': u'',
            u'export_results': u'export',
        }
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        self.client.get(url)
        # Searching date range with unique doc1 keys
        response = self.client.post(url, search_MDT_5_export_results_test)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)

        # Response is ok and no warning exists there
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        # Response is type CSV and contains proper docs
        self.assertEqual(response._headers['content-type'][1], 'text/csv')
        self.assertContains(response, self.edit_document_name_4)
        self.assertContains(response, self.edit_document_name_1)
        self.assertContains(response, self.edit_document_name_5)
        self.assertNotContains(response, 'ADL-')
        self.assertContains(response, 'Employee,Andrew')
        # Contains secondary key (Refs Bug #941)
        self.assertContains(response, 'Test Document Number 2 for MDT 5')
        self.assertContains(response, 'Employee,Andrew')

    def test_63_mdt_search_contains_mdt_name_in_header(self):
        """
        Feature #800: MUI: Show document type in search options

        Testing here if MDT search contains MDT name in header.
        """
        test_mdt_id_5_name = 'mdt5'
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        # MDT5 name present in response (step name header)
        mdt_name = test_mdt_id_5_name.capitalize()
        self.assertContains(response, mdt_name+' Search Options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, self.search_MDT_5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and no warning exists there
        self.assertEqual(response.status_code, 200)
        # MDT5 name present in response (step name header)
        self.assertContains(response, test_mdt_id_5_name.capitalize()+' Results')

    def test_64_docrule_search_contains_docrule_name_in_header(self):
        """
        Feature #800: MUI: Show document type in search options

        Testing here if DocumentType based search contains Document Type name in header.
        """
        # Setting DocumentTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and no warning exists there
        self.assertEqual(response.status_code, 200)
        # Response contains proper step header
        self.assertContains(response, 'Adlibre invoices Search Options')
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        # Feel free to replace it with any other search
        data = self.date_range_1and2_not3
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response contains proper step header
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adlibre invoices Results")

    def test_65_search_results_sorting(self):
        """Refs #766 MUI: Sortable Search Results"""
        unordered_docs = [self.edit_document_name_4, self.edit_document_name_1, self.edit_document_name_5]
        descending_test1 = [self.edit_document_name_1, self.edit_document_name_4, self.edit_document_name_5]
        ascending_date1 = [self.edit_document_name_5, self.edit_document_name_4, self.edit_document_name_1]
        descending_description = [self.edit_document_name_5, self.edit_document_name_1, self.edit_document_name_4]
        sort1_query1 = {"order": "icon-chevron-up",
                        "sorting_key": "Tests Uppercase Field", }
        sort1_query2 = {"order": "icon-chevron-down",
                        "sorting_key": "Tests Uppercase Field", }
        sort2_query1 = {"order": "icon-chevron-up",
                        "sorting_key": "Creation Date", }
        sort2_query2 = {"order": "icon-chevron-down",
                        "sorting_key": "Creation Date", }
        sort3_query1 = {"order": "icon-chevron-up",
                        "sorting_key": "Description", }
        sort3_query2 = {"order": "icon-chevron-down",
                        "sorting_key": "Description", }
        # Getting normal default results
        url = reverse('mdtui-search')
        response = self.client.post(url, self.select_mdt5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee')
        response = self.client.post(new_url, self.search_MDT_5)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        # Proper response check (Just in case...)
        self.assertContains(response, self.edit_document_name_5)
        self.assertNotContains(response, self.edit_document_name_3)
        self.assertNotContains(response, self.edit_document_name_2)
        self.assertContains(response, self.edit_document_name_1)
        self.assertContains(response, self.edit_document_name_4)
        self.assertNotContains(response, self.edit_document_name_6)
        # Checking order we have here (default order)
        code_order = self._check_search_results_order(response)
        self.assertEqual(code_order, unordered_docs)
        # Getting new ordered list of docs
        self._check_sorting_order_results(results_url, sort1_query1, unordered_docs)
        # Getting docs in descending order now with docs without this key in the bottom of results
        self._check_sorting_order_results(results_url, sort1_query2, descending_test1)
        # Getting docs in ascending order sorting by Creation Date
        self._check_sorting_order_results(results_url, sort2_query1, ascending_date1)
        # Descending order by Creation Date
        self._check_sorting_order_results(results_url, sort2_query2, descending_test1)
        # Description sorting ascending
        self._check_sorting_order_results(results_url, sort3_query1, unordered_docs)
        # Description sorting descending
        self._check_sorting_order_results(results_url, sort3_query2, descending_description)

    def test_66_edit_document_indexes_access(self):
        """
        Refs #764 - Feature: MUI Edit Metadata

        Check for button "Edit document Indexes" rendering depending on user permission to edit.
        Checks:
        - permitted user
        - superuser
        - not permitted user
        """
        edit_btn_string = """href="/mdtui/edit/%s""" % self.edit_document_name_1
        data = {'mdt': self.test_mdt_id_5}
        # Adding apecial permission to test user 1
        user = User.objects.get(username=self.username_1)
        # Registering that user in required security groups and removing their permissions...
        g, created = Group.objects.get_or_create(name=SEC_GROUP_NAMES['edit_index'])
        if created:
            g.save()
        g.user_set.add(user)
        for perm in g.permissions.all():
            g.permissions.remove(perm)
        # Logging in with this user
        self.client.logout()
        self.client.login(username=self.username_1, password=self.password_1)
        # Selecting MDT
        url = reverse('mdtui-search-type')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # User can see Desired Field
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Employee")
        url = reverse('mdtui-search-options')
        # Searching docs for MDT5
        response = self.client.post(url, self.search_MDT_5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # Response contains documents and edit button for them
        self.assertContains(response, self.edit_document_name_1)
        self.assertContains(response, edit_btn_string)

        # Checking Superuser perms now
        self.client.logout()
        self.client.login(username=self.username, password=self.password)
        # Simplified search sequence, assuming all checked working before.
        url = reverse('mdtui-search-type')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        response = self.client.post(url, self.search_MDT_5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # Response contains documents and edit button for them
        self.assertContains(response, self.edit_document_name_1)
        self.assertContains(response, edit_btn_string)

        # Checking user without permissions now (Creating one first)
        user = User.objects.create_user(self.username_4, 'b@c.com', self.password_4)
        user.save()
        # Adding permission to interact Test Doc Type 3 only
        perm = Permission.objects.filter(name=u'Can interact Test Doc Type 3')
        user.user_permissions.add(perm[0])
        # Registering that user in required security groups and removing their permissions...
        for groupname in ['security', 'MUI Search interaction']:
            g = Group.objects.get(name=groupname)
            g.user_set.add(user)
            for perm in g.permissions.all():
                g.permissions.remove(perm)
        # Relogin with this user
        self.client.logout()
        self.client.login(username=self.username_4, password=self.password_4)
        # Simplified search sequence, assuming all checked working before.
        url = reverse('mdtui-search-type')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        response = self.client.post(url, self.search_MDT_5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # Response contains documents and edit button for them
        self.assertContains(response, self.edit_document_name_1)
        self.assertNotContains(response, edit_btn_string)
        self.assertNotContains(response, self.edit_document_name_5)  # We're not under admin now

    def test_67_edit_document_indexes_step_rendered_properly(self):
        """
        Refs #764 - Feature: MUI Edit Metadata

        Uses documents 'CCC-0001' and 'BBB-0002' to check:
        - Edit step head rendered properly
        - Contains all the form fields it should
        - Form is filled with proper data
        """
        self._check_edit_step_with_document(self.edit_document_name_1,  self.m5_doc1_dict)
        self._check_edit_step_with_document(self.edit_document_name_2, self.m2_doc1_dict)

    def test_68_edit_document_indexes_updating_index(self):
        """
        Refs #764 - Feature: MUI Edit Metadata

        - Uppercase field still forces uppercase
        - secondary keys stored OK
        - Main fields (description) keys stored ok
        - Form changes data in the couchdb document itself
        """
        new_m5_doc1_dict = {
            'description': 'Editing of builtin field test',
            'Employee': 'Andrew and his friend',
            'Tests Uppercase Field': 'some data',
        }
        self._check_edit_step_with_document(self.edit_document_name_1,  self.m5_doc1_dict)
        ids = self._read_indexes_form(self.response)
        data = self._create_edit_indexes_post_dict(new_m5_doc1_dict, ids)
        url = reverse('mdtui-edit', kwargs={'code': self.edit_document_name_1})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.edit_document_name_1)
        # EDIT Results page contains all OLD indexes
        for key, value in self.m5_doc1_dict.iteritems():
            if not key == 'date':
                if not value == 'some data':
                    self.assertContains(response, value)
        # EDIT Results page contains all NEW indexes
        for value in new_m5_doc1_dict.itervalues():
            if not value == 'some data':
                self.assertContains(response, value)
            else:
                self.assertContains(response, 'SOME DATA')
        # POST to save those indexes
        self.client.post(reverse('mdtui-edit-finished'), {'something': ' '})
        # Quering CouchDB directly for existence and proper document indexes rendering
        couch_doc = self._open_couchdoc(self.couchdb_name, self.edit_document_name_1)
        if not 'index_revisions' in couch_doc:
            raise AssertionError('CouchDB Document has not been updated')
        if not '1' in couch_doc['index_revisions']:
            raise AssertionError('CouchDB Document index_revisions has no revisions')

    def test_69_edit_document_indexes_updating_index(self):
        """
        Refs #764 - Feature: MUI Edit Metadata

        Refs #824 - Bug: Editing document indexes displays wrong dates in old doc indexes
        Refs #822 - Bug: Edit indexes new revision writes down wrong date to secindary indexes
        Refs #823 - Bug: Adding new document revision (file, e.g. by API) removes indexes revision

        - Uppercase field still forces uppercase
        - secondary keys stored OK
        - Main fields (description) keys stored ok
        - field type DATE in CouchDB document stored properly after update indexes
        - document indexes revision updates to v2 after second update
        """
        new_m2_doc1_dict = {
            'description': 'Test Document MDT 3 Number 1 and other',
            'Employee': 'Vovan Patsan',
            'Reporting Entity': 'JTG',
            'Report Type': 'Reconciliation',
            'Report Date': '02/04/2012',
            'Additional': 'Something mdt2 1'
        }
        doc_used = self.edit_document_name_2
        self._check_edit_step_with_document(doc_used, self.m2_doc1_dict)
        ids = self._read_indexes_form(self.response)
        data = self._create_edit_indexes_post_dict(new_m2_doc1_dict, ids)
        url = reverse('mdtui-edit', kwargs={'code': doc_used})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, doc_used)
        # EDIT Results page contains all OLD indexes
        for key, value in self.m2_doc1_dict.iteritems():
            if not key == 'date':
                self.assertContains(response, value)
        # EDIT Results page contains all NEW indexes
        for value in new_m2_doc1_dict.itervalues():
            self.assertContains(response, value)
        # POST to save those indexes
        self.client.post(new_url,  {'something': ' '})
        # Quering CouchDB directly for existence and proper document indexes rendering
        couch_doc = self._open_couchdoc(self.couchdb_name, doc_used)
        if not 'index_revisions' in couch_doc:
            raise AssertionError('CouchDB Document has not been updated')
        if not '1' in couch_doc['index_revisions']:
            raise AssertionError('CouchDB Document index_revisions has no revisions')
        if '2' in couch_doc['index_revisions']:
            raise AssertionError('CouchDB Document Should have only one revision at this step')
        if not couch_doc['mdt_indexes']['Report Date'] == u'2012-04-02T00:00:00Z':
            raise AssertionError('CouchDB Document has bug storing new indexes DATE format')
        # Adding revision 2 of document indexes
        data = self._create_edit_indexes_post_dict(new_m2_doc1_dict, ids)
        url = reverse('mdtui-edit', kwargs={'code': doc_used})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # POST to save those indexes
        self.client.post(new_url,  {'something': ' '})
        # Checking if revision 2 of CouchDB document indexes created
        couch_doc = self._open_couchdoc(self.couchdb_name, doc_used)
        if not '2' in couch_doc['index_revisions']:
            raise AssertionError('CouchDB Document does not update indexes revisions after more than 1 edit')
        if '2' in couch_doc['revisions']:
            raise AssertionError('Document has revision 2 already. can not test farther')
        # Checking upload file by API to ensure revision indexes out there after document revision update
        self.test_document_files_dir = os.path.join(settings.FIXTURE_DIRS[0], 'testdata')
        file_path = os.path.join(self.test_document_files_dir, doc_used + '.pdf')
        data = {'file': open(file_path, 'r')}
        url = reverse('api_file', kwargs={'code': doc_used, 'suggested_format': 'pdf'})
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)
        # Checking if revision 2 of CouchDB document indexes preserved
        couch_doc = self._open_couchdoc(self.couchdb_name, doc_used)
        if not '2' in couch_doc['index_revisions']:
            raise AssertionError('CouchDB Document fails to preserve index_revisions upon document revision update.')
        if not '2' in couch_doc['revisions']:
            raise AssertionError('Document has not been updated by API. Something went wrong there.')

    def test_70_only_DMS_superuser_sees_admin_entry_menu_title(self):
        """ Superuser only has shortcut in me to acces django admin"""
        url = reverse('mdtui-home')
        django_admin_btn_name = 'DMS Admin'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, django_admin_btn_name)
        # Relogin with simple user (not superuser)
        self.client.logout()
        self.client.login(username=self.username_1, password=self.password_1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, django_admin_btn_name)

    def test_71_edit_document_indexes_updating_index(self):
        """
        Refs #829 Bug: Files Secondary indexes contain username and user PK

        - Tests only proper indexes exist in secondary indexes of document that has more than 1 file revision
        """
        # Using document that has more than 1 revision for this test.
        couch_doc = self._open_couchdoc(self.couchdb_name, self.doc1)
        if not '2' in couch_doc['revisions'].iterkeys():
            raise AssertionError('CouchDB Document Has insufficient amount of revisions for test (required > 1 )')
        if 'metadata_user_id' in couch_doc['mdt_indexes']:
            raise AssertionError("""CouchDB Document's secondary indexes Contains wrong indexes: "metadata_user_id" """)
        if 'metadata_user_name' in couch_doc['mdt_indexes']:
            raise AssertionError("""CouchDB Document secondary indexes Contains wrong indexes: "metadata_user_name" """)

    def test_72_redirect_after_successful_edit(self):
        """
        Refs #832 Edit indexes preserves META_HTTP_REFERER url through whole process
        Refs #833: Edit document indexes new error handling	New	Iurii Garmash
        Refs #834: Save happens in final step (after save pressed)
        """
        new_m5_doc2_dict = {
            'description': 'Something new here',
            'Employee': 'Yuri',
            'Tests Uppercase Field': 'something more',
        }
        doc_name = self.edit_document_name_4
        # SEARCH for doc
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        self.client.get(url)
        # Searching date range with unique doc1 keys
        response = self.client.post(url, self.search_MDT_5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and only one doc persists there
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, doc_name)

        # EMULATE click to EDIT a document
        search_url = new_url
        url = reverse('mdtui-edit', kwargs={'code': doc_name})
        response = self.client.get(url, {}, HTTP_REFERER=search_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, doc_name)
        ids = self._read_indexes_form(response)
        data = self._create_edit_indexes_post_dict(new_m5_doc2_dict, ids)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'About to store index data for document')
        # Trying to go back and forth to emulate user possibilities properly
        self.client.get(url)
        self.client.get(new_url)
        # POST to save those indexes
        response = self.client.post(new_url,  {'something': ' '})
        self.assertEqual(response.status_code, 302)
        # Redirect follows referrer specified (where we came into edit indexes)
        old_url = self._retrieve_redirect_response_url(response)
        self.assertEqual(old_url, search_url)
        # Returning to results render error
        response = self.client.get(new_url)
        self.assertContains(response, MDTUI_ERROR_STRINGS['ERROR_EDIT_INDEXES_FINISHED'])

    def test_73_preserving_editing_indexes_only_where_needed(self):
        """
        Refs #835 Edit metadata provides wrong file index

        New indexes were not loading for second and each new doc.
        Indexes should persist if returning from "edit indexes result" URL.
        If referrer is other URL or absent... load only Document's indexes.
        """
        first_doc_name = self.edit_document_name_1
        second_doc_name = self.edit_document_name_4
        first_doc_new_indexes = {
            '0': 'SOME DATA',
            '1': '4',
            '2': 'Andrew and his friend',
            'description': 'Editing of builtin field test',
        }
        second_doc_new_indexes = {
            '0': 'SOME OTHER DATA',
            '1': '4',
            '2': 'Andrew',
            'description': 'Test Document Number 2 for MDT 5',
        }
        first_only_should_contain = 'Andrew and his friend'
        # Checking first document for unique index
        url = reverse('mdtui-edit', kwargs={'code': first_doc_name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response2 = self.client.post(url, first_doc_new_indexes)
        self.assertEqual(response2.status_code, 302)
        response = self.client.get(url)
        self.assertContains(response, first_doc_name)
        self.assertContains(response, first_only_should_contain)
        # Checking second document should not contain this index
        url = reverse('mdtui-edit', kwargs={'code': second_doc_name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response2 = self.client.post(url, second_doc_new_indexes)
        self.assertEqual(response2.status_code, 302)
        response = self.client.get(url)
        self.assertContains(response, second_doc_name)
        self.assertNotContains(response, first_only_should_contain)
        # Checking first doc now contains those indexes
        url = reverse('mdtui-edit', kwargs={'code': first_doc_name})
        response = self.client.get(url, {}, HTTP_REFERER='http://127.0.0.1/'+reverse('mdtui-edit-finished'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first_doc_name)
        self.assertNotContains(response, first_only_should_contain)

    def test_74_typeahead_working_in_edit_indexes(self):
        """
        Refs #836 Typeahead not working with single key (non parallel) field.

        The issue was deeper and, in fact, is about providing sufficient initial data for autocomplete view.
        """
        doc_name = self.edit_document_name_1
        new_indexes = {
            '0': 'SOME DATA',
            '1': '1',
            '2': 'Andrew and his friend',
            'description': 'Editing of builtin field test',
        }
        typ_call_1 = {
            'key_name': 'Tests Uppercase Field',
            'autocomplete_search': 'SOME DAT',
        }
        typ_call_2 = {
            'key_name': 'Employee',
            'autocomplete_search': 'Andre',
        }
        # Checking first document for unique index
        url = reverse('mdtui-edit', kwargs={'code': doc_name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response2 = self.client.post(url, new_indexes)
        self.assertEqual(response2.status_code, 302)
        response = self.client.get(url, {}, HTTP_REFERER=reverse('mdtui-edit-finished'))
        self.assertContains(response, doc_name)
        self.assertContains(response, new_indexes['description'])
        # Checking typeahead now will provide proper results.
        typ_url = reverse('mdtui-parallel-keys')
        response = self.client.post(typ_url, typ_call_1)
        for value in typ_call_1.itervalues():
            self.assertContains(response, value)
        typ_url = reverse('mdtui-parallel-keys')
        response = self.client.post(typ_url, typ_call_2)
        for value in typ_call_2.itervalues():
            self.assertContains(response, value)

    def test_75_paginator_exists(self):
        """Refs #805: Simple paginator rendering test"""
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        self.client.get(url)
        response = self.client.post(url, self.search_MDT_5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'results matching query.')
        self.assertContains(response, 'Page')
        self.assertContains(response, '/mdtui/search/results?page=1">1')   # Paginator page one present
        self.assertNotContains(response, 'Next')   # Paginator page next

    def test_76_search_includes_ending_date_range_variable(self):
        """
        Refs bug #840 Search date range with one date bug

        checks that search is including document with finish date range date.

        only one record in a range and creation date is one date.. then records of this, finish range date, are found...
        bug results example:
        e.g. search for CON creation date 10/08/12 - 11/08/12 no records for date 11/08/12,
        but if you select 10/08/12 - 12/08/12 you find it.
        """
        search_MDT_5_date_range_end_date = {
            u'date': u'01/03/2012',
            u'end_date': u'10/03/2012',
            u'0': u'Andrew',
        }
        search_MDT_5_date_range_end_date2 = {
            u'date': u'01/03/2012',
            u'end_date': u'09/03/2012',
            u'0': u'Andrew',
        }
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        self.client.get(url)
        # Searching date range for this test
        response = self.client.post(url, search_MDT_5_date_range_end_date)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and only one doc persists there
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        # No documents for any of docrules found in response
        self.assertNotContains(response, 'BBB-')
        self.assertNotContains(response, self.edit_document_name_1)
        self.assertNotContains(response, 'ADL-')
        self.assertNotContains(response, self.edit_document_name_4)

        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        self.client.get(url)
        # Searching date range for this test
        response = self.client.post(url, search_MDT_5_date_range_end_date2)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        # Response is ok and only one doc persists there
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        # No documents for any of docrules found in response
        self.assertNotContains(response, 'BBB-')
        self.assertNotContains(response, self.edit_document_name_1)
        self.assertNotContains(response, 'ADL-')
        self.assertNotContains(response, self.edit_document_name_4)

    def test_77_indexing_date_rendering(self):
        """Refs #786 Checking if 'Creation date' Rendered properly in both index and search."""
        # Testing search results for proper rendering
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = self.date_range_none
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Real data check
        self.assertContains(response, """Creation Date: (from: 30/03/2012 to: 31/03/2012)""")
        self.assertNotContains(response, "end_date")
        self.assertNotContains(response, "Undefined")

    def test_78_forbidden_indexes_adding_restrictions(self):
        """
        Refs #700 Feature: MDT/MUI fixed choice index fields

        Fully tests part 2 of this feature
        (with warning and blocking farther document upload for new indexes)
        """
        # Modified doc1 dict for our needs
        test_doc_dict = self.doc1_dict_forbidden_indexes
        # Changing MDT to have 1 admincreate perms field.
        operating_mdt = 'mdt2'
        mdt = MetaDataTemplate.get(docid=operating_mdt)
        mdt.fields[u'1'][u'create_new_indexes'] = u'open'
        mdt.fields[u'2'][u'create_new_indexes'] = u'admincreate'
        mdt.save()

        # Check new indexes are normally added with admin priviledges.
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NEW_KEY_VALUE_PAIR']+'Employee Name: Someone Special')
        self.assertContains(response, MDTUI_ERROR_STRINGS['NEW_KEY_VALUE_PAIR']+'Employee ID: 1234567890')
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['ADMINLOCKED_KEY_ATTEMPT'])

        # Relogin with non admin user
        self.client.logout()
        self.client.login(username=self.username_2, password=self.password_2)

        # Check new indexes are disabling the upload form with non staff/admin person
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 200)
        for value in test_doc_dict.itervalues():
            self.assertContains(response, value)
        self.assertContains(response, MDTUI_ERROR_STRINGS['ADMINLOCKED_KEY_ATTEMPT']+'Employee Name')

        # Making this field locked
        mdt.fields[u'2'][u'create_new_indexes'] = u'locked'
        mdt.save()

        # Check both admin and non admin can not add new values to locked key
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MDTUI_ERROR_STRINGS['LOCKED_KEY_ATTEMPT']+'Employee Name')

        self.client.logout()
        self.client.login(username=self.username, password=self.password)

        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MDTUI_ERROR_STRINGS['LOCKED_KEY_ATTEMPT']+'Employee Name')

        # Cleaning up MDT for farther tests
        del mdt.fields[u'1'][u'create_new_indexes']
        del mdt.fields[u'2'][u'create_new_indexes']
        mdt.save()

    def _78_test_helper(self, test_doc_dict):
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, test_doc_dict)
        response = self.client.post(url, post_dict)
        return response

    def test_79_indexes_persistent_after_revisit_on_indexing_form(self):
        """Refs #869 MUI Improvement Indexing Step2 Indexes values

        Values stay after submitting them and returning for step 2 again.
        e.g. to correct any value or because of non field form errors"""
        # Selecting Document Type Rule
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {self.test_mdt_docrule_id: 'docrule'})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc1_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # check indexes on next page
        for key in rows_dict.iterkeys():
            self.assertContains(response, key)
        for key in post_dict.itervalues():
            self.assertContains(response, key)
        # Going back to step 2 (adding indexes form) and checking if it's populated.
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        for key, value in post_dict.iteritems():
            self.assertContains(response, key)

    def test_80_forbidden_indexes_adding_and_group(self):
        """Refs #935 part 1. MDT/MUI fixed choice index fields (improving the workflow)"""
        test_doc_dict = self.doc1_dict_forbidden_indexes
        # Changing MDT to have 1 admincreate perms field.
        operating_mdt = 'mdt2'
        mdt = MetaDataTemplate.get(docid=operating_mdt)
        mdt.fields[u'1'][u'create_new_indexes'] = u'open'
        mdt.fields[u'2'][u'create_new_indexes'] = u'admincreate'
        mdt.save()

        # Check new indexes are normally added with admin priviledges.
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NEW_KEY_VALUE_PAIR']+'Employee Name: Someone Special')
        self.assertContains(response, MDTUI_ERROR_STRINGS['NEW_KEY_VALUE_PAIR']+'Employee ID: 1234567890')
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['ADMINLOCKED_KEY_ATTEMPT'])

        # Relogin with non admin user
        self.client.logout()
        self.client.login(username=self.username_2, password=self.password_2)

        # Check new indexes are disabling the upload form with non staff/admin person
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 200)
        for value in test_doc_dict.itervalues():
            self.assertContains(response, value)
        self.assertContains(response, MDTUI_ERROR_STRINGS['ADMINLOCKED_KEY_ATTEMPT']+'Employee Name')

        # Registering that user in required security groups...
        user = User.objects.filter(username=self.username_2)
        g = Group.objects.get(name=SEC_GROUP_NAMES['edit_fixed_indexes'])
        g.user_set.add(user[0])

        # Check if redirect == Means success.
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 302)

    def test_81_locked_indexes_field_works_for_non_admin(self):
        """Refs #956 User cannot select an existing locked index

        Issue with non admin user can not add an existing key into DMS Indexing when key is set to admincreate
        """
        test_doc_dict = self.doc1_dict_existing_indexes
        username_7 = 'tests_user_7'
        password_7 = 'test7'
        # Creating special user
        user = User.objects.create_user(username_7, 'a@b.com', password_7)
        user.save()
        # Registering that user in required security groups and removing their permissions...
        for groupname in ['security', 'api', 'MUI Index interaction', 'MUI Search interaction']:
            g = Group.objects.get(name=groupname)
            g.user_set.add(user)
        self.client.logout()
        self.client.login(username=username_7, password=password_7)
        # Check existing indexes are normally added with NON aprivileges.
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NEW_KEY_VALUE_PAIR'] + 'Employee ID: 1234567890')
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['ADMINLOCKED_KEY_ATTEMPT'])
        # Now checking that modified Keys are not passing through.
        new_key = test_doc_dict['Employee Name'] + 's'
        test_doc_dict['Employee Name'] = new_key
        response = self._78_test_helper(test_doc_dict)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MDTUI_ERROR_STRINGS['ADMINLOCKED_KEY_ATTEMPT'])
        self.assertNotContains(response, MDTUI_ERROR_STRINGS['NEW_KEY_VALUE_PAIR'] + 'Employee ID: 1234567890')
        self.assertContains(response, new_key)

    def test_82_search_by_mdt_without_indexes(self):
        """Check for ability to view document without indexes.

        Refs #816 (MDT's on the demo server so that we can search for the uploaded images)
        Refs #945 Barcode Scanner Test MUI Results Colums
        """
        # Should be day before due to tests issues with timezones AU/UA.
        prev_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(settings.DATE_FORMAT)
        todays_range = {u'date': prev_date}
        test_doc1 = 'TST00000001'
        test_doc2 = 'TST00000002'
        # Uploading barcode (Image file into API)
        self._api_upload_file(test_doc1, suggested_format='jpeg')
        # Uploading and updating second doc to make second revision
        self._api_upload_file(test_doc2, suggested_format='jpeg')
        self._api_upload_file(test_doc2, suggested_format='jpeg', update=True)

        # Setting Barcode docrule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id4}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, todays_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "You have not defined Document Searching Options")
        self.assertContains(response, todays_range[u'date'])
        self.assertContains(response, test_doc1)
        self.assertContains(response, test_doc2)
        # document with no indexes and mre than 1 revision rendered properly by MUI
        self.assertNotContains(response, "metadata_doc_type_rule_id")
        self.assertNotContains(response, "mdt_indexes")
        self.assertNotContains(response, "metadata_created_date")
        self.assertNotContains(response, "tags")

        # Found Image rendered properly instead of pdf viewer:
        url = reverse('mdtui-view-object', kwargs={'code': test_doc1})
        response = self.client.get(url)
        self.assertContains(response, 'img src="/api/new_file/TST00000001"')

    def test_83_can_sort_improper_indexes(self):
        """
        Refs #948 Internal Server Error: /mdtui/search/results
        Will change one document's index and try to sort it in results response
        """
        mdt5_docs_range = {'date': '10/03/2012',
                           'end_date': '13/03/2012'}
        first_doc = self.edit_document_name_1
        second_doc = self.edit_document_name_4
        sorting_dict = {'sorting_key': 'Employee',
                        'order': 'icon-chevron-up'}
        # modifying couchdoc to get emulation of mistyped user (entering wrong data type into this index field)
        couchdoc = CouchDocument.get(docid=second_doc)
        previous_value = couchdoc['mdt_indexes'][u'Employee']
        couchdoc['mdt_indexes'][u'Employee'] = mdt5_docs_range['date']
        couchdoc.save()
        # setting MDT
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching date range with unique doc1 keys
        response = self.client.post(url, mdt5_docs_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # Searching keys exist in search results
        self.assertContains(response, mdt5_docs_range['date'])
        self.assertContains(response, mdt5_docs_range['end_date'])
        self.assertContains(response, first_doc)
        self.assertContains(response, second_doc)
        # trying new sorting causes no errors
        response = self.client.post(new_url, sorting_dict)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first_doc)
        self.assertContains(response, second_doc)
        # Cleanup to previous state
        couchdoc['mdt_indexes'][u'Employee'] = previous_value
        couchdoc.save()

    def test_84_improper_date_range_search(self):
        """Refs #896 CORE: search bug with output for invalid ranges

        When any date ranage has "To" date less than "From" date.
        """
        wrong_date_range1 = {
            'date': '13/03/2012',
            'end_date': '10/03/2012'
        }
        # Testing date range for "Creation Date"
        url = reverse('mdtui-search-type')
        data = {'mdt': self.test_mdt_id_5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        response = self.client.post(url, wrong_date_range1)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'ADL-')
        self.assertNotContains(response, 'BBB-')
        self.assertNotContains(response, 'CCC-')
        self.assertNotContains(response, 'TST0')
        self.assertContains(response, SEARCH_ERROR_MESSAGES['wrong_indexing_date'])

        wrong_date_range2 = {
            '0': '',
            '1': '',
            '3': '',
            '4': '',
            '5': '',
            '2_from': '25/03/2012',
            '2_to': '01/03/2012',
            'date': '',
            'end_date': '',
            'export_results': '',
        }
        # Testing secondary key date range
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        response = self.client.post(url, wrong_date_range2)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'ADL-')
        self.assertContains(response, SEARCH_ERROR_MESSAGES['wrong_date'])

    def test_85_choice_type_field(self):
        """
        Refs #700 Feature: MDT/MUI fixed choice index fields
        """
        # TODO: Make testing of search and adding indexes for documents with choice fields.
        pass

    def test_86_editing_document_type_UI(self):
        """Refs #957 Ability to change Document Type: UI part"""
        # Button to change type is properly rendered
        edit_doc_name = self.edit_document_name_4
        edit_inexistent_doc = self.edit_document_name_7
        edit_doc_decription = 'Something new here'
        same_docrule = {'docrule': '8'}
        url = reverse('mdtui-edit', kwargs={'code': edit_doc_name})
        response = self.client.get(url)
        self.assertContains(response, edit_doc_name)
        self.assertContains(response, edit_doc_decription)
        self.assertContains(response, 'Change Document Type')  # Button caption
        ch_type_url = reverse('mdtui-edit-type', kwargs={'code': edit_doc_name})
        response = self.client.get(ch_type_url)
        self.assertContains(response, 'Document Type:')
        self.assertContains(response, edit_doc_name)
        self.assertContains(response, 'selected')  # Has a preselected docrule
        self.assertContains(response, MDTUI_ERROR_STRINGS['EDIT_TYPE_WARNING'])
        # Selecting same docrule for this document
        response = self.client.post(ch_type_url, same_docrule)
        self.assertContains(response, MDTUI_ERROR_STRINGS['EDIT_TYPE_ERROR'])
        self.assertContains(response, url)  # Back button working and rendered properly
        # Wrong document passed to view
        ch_type_url = reverse('mdtui-edit-type', kwargs={'code': edit_inexistent_doc})
        response = self.client.get(ch_type_url)
        self.assertEqual(response.status_code, 200)

    def test_87_editing_document_move_document(self):
        """Refs #957 Ability to change Document Type: Core logic"""
        edit_doc_name = self.edit_document_name_4
        new_doc_name = self.edit_document_name_7
        new_doc_revision_prefix = '_r1.pdf'
        edit_doc_decription = 'Something new here'
        secondary_index = 'SOMETHING MORE'
        secondary_key = 'Reporting Entity'
        renaming_docrule = {'docrule': '7'}

        ch_type_url = reverse('mdtui-edit-type', kwargs={'code': edit_doc_name})
        # HACK: docrule sequence fixup.
        docrule = DocumentTypeRule.objects.get(pk=int(renaming_docrule['docrule']))
        docrule.sequence_last = 3
        docrule.save()

        response = self.client.post(ch_type_url, renaming_docrule)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertContains(response, new_doc_name)
        self.assertContains(response, edit_doc_decription)
        self.assertContains(response, secondary_key)  # Form rendered
        self.assertNotContains(response, secondary_index)

        # Testing couchdb document with indexes generated properly
        couch_doc = self._open_couchdoc(self.couchdb_name, new_doc_name)
        self.assertEqual(couch_doc['revisions']['1']['name'], new_doc_name + new_doc_revision_prefix)  # Revisions OK
        self.assertEqual(couch_doc['index_revisions']["2"]['mdt_indexes']["Employee"], "Yuri")  # Index Revisions OK
        self.assertEqual(couch_doc['metadata_description'], edit_doc_decription)  # Description OK

    def test_88_edit_document_revisions(self):
        """Refs #890 When editing metadata allow user to add new document revision"""
        doc_name = self.doc1
        edit_revisions_list = [
            # keys
            'Revision:',
            'Filename:',
            'Compression:',
            'File Type:',
            'Created:',
            # values
            'application/pdf',
            'GZIP',
            # files
            'ADL-0001_r1.pdf',
            'ADL-0001_r2.pdf',
            # buttons
            'Upload New Revision',
            'View',
            'Finish',
        ]
        wrong_code = 'ADL-0100'
        creating_doc = 'ADL-0001_r3.pdf'
        # Edit doc indexes has this button
        edit_doc_url = reverse('mdtui-edit', kwargs={'code': doc_name})
        edit_revisions_url = reverse('mdtui-edit-revisions', kwargs={'code': doc_name})
        edit_response = self.client.get(edit_doc_url)
        self.assertContains(edit_response, edit_revisions_url)
        # Errors not causing view problems
        wrong_response = self.client.get(reverse('mdtui-edit-revisions', kwargs={'code': wrong_code}))
        self.assertContains(wrong_response, MDTUI_ERROR_STRINGS['NO_DOC'])
        # Edit revisions page proper rendering
        revisions_response = self.client.get(edit_revisions_url)
        self.assertContains(revisions_response, edit_doc_url)  # Has back button
        for key in edit_revisions_list:
            if not key in revisions_response.content:
                raise self.failureException('Key: %s is not present in response' % key)
        if creating_doc in revisions_response:
            raise self.failureException('Can not test farther because filename: %s already exists' % creating_doc)
        # Testing file upload
        file_path = os.path.join(self.test_document_files_dir, doc_name + '.pdf')
        data = {'file': open(file_path, 'r')}
        new_revisions_response = self.client.post(edit_revisions_url, data)
        self.assertEqual(new_revisions_response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(new_revisions_response)
        response = self.client.get(new_url)
        self.assertContains(response, creating_doc)

    def test_89_mark_document_deleted(self):
        """Refs #827 Mark document deleted view and actions"""
        testdoc1 = self.doc1
        redir_url = 'http://testserver/mdtui/'
        url1 = reverse('mdtui-edit-delete', kwargs={'code': testdoc1})
        response = self.client.post(url1)
        self.assertEqual(response.status_code, 302)
        redir_url1 = self._retrieve_redirect_response_url(response)
        self.assertEqual(redir_url1, redir_url)
        mark_deleted_doc = self._open_couchdoc(self.couchdb_name, testdoc1)
        if not 'deleted' in mark_deleted_doc.iterkeys() and mark_deleted_doc['deleted'] != 'deleted':
            raise AssertionError('Did not really mark document deleted: %s' % testdoc1)
        test_couchdoc1 = self._open_couchdoc(self.couchdb_name, testdoc1, view_name='dmscouch/all')
        if test_couchdoc1:
            raise AssertionError('Did not really mark document deleted in CouchDB: %s' % testdoc1)
        test_couchdoc1 = self._open_couchdoc(self.couchdb_name, testdoc1, view_name='dmscouch/deleted')
        if not test_couchdoc1:
            raise AssertionError('Document is not present in CouchDB deleted documents view: %s' % testdoc1)

    def test_90_mark_document_deleted_from_search_workflow(self):
        """Refs #827 Mark document deleted view and actions"""
        not_existing_doc = self.doc1
        existing_doc = self.doc2
        remaining_doc = self.doc3
        url = reverse('mdtui-search')
        # Selecting ADL docrule
        response = self.client.post(url, self.select_docrule_2)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Friends Name')
        # Posting ADL docs range
        response = self.client.post(new_url, self.date_range_all_ADL)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, not_existing_doc)
        self.assertContains(response, existing_doc)
        self.assertContains(response, remaining_doc)
        # Going to edit document revisions to look for client redirect and data shown to user
        edit_url = reverse('mdtui-edit', kwargs={'code': existing_doc})
        response = self.client.get(edit_url, HTTP_REFERER=results_url)
        self.assertEqual(response.status_code, 200)
        edit_rev_url = reverse('mdtui-edit-revisions', kwargs={'code': existing_doc})
        response = self.client.get(edit_rev_url)
        t = existing_doc + '_r1.pdf'
        self.assertContains(response, t)
        delete_url = reverse('mdtui-edit-delete', kwargs={'code': existing_doc})
        response = self.client.post(delete_url)
        # Redirects to search after delete and search results are updated
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertNotContains(response, not_existing_doc)
        self.assertNotContains(response, existing_doc)
        self.assertContains(response, remaining_doc)
        # Edit document views hide this doc too.
        response = self.client.get(edit_rev_url)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_DOC'])
        response = self.client.get(edit_url)
        self.assertContains(response, MDTUI_ERROR_STRINGS['NO_DOC'])

    def test_91_mark_revision_deleted(self):
        """Refs #827 Mark document deleted view and actions"""
        existing_doc = self.edit_document_name_2
        deleting_revision = '2'
        remaining_revision = '1'
        url = reverse('mdtui-search')
        # Selecting ADL docrule
        response = self.client.post(url, self.select_docrule_7)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporting Entity')
        # Posting ADL docs range
        response = self.client.post(new_url, self.date_range_all_ADL)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, existing_doc)
        # Going to edit document revisions to look for client redirect and data shown to user
        edit_url = reverse('mdtui-edit', kwargs={'code': existing_doc})
        response = self.client.get(edit_url, HTTP_REFERER=results_url)
        self.assertEqual(response.status_code, 200)
        edit_rev_url = reverse('mdtui-edit-revisions', kwargs={'code': existing_doc})
        response = self.client.get(edit_rev_url)
        t = existing_doc + '_r%s.pdf' % deleting_revision
        t_existing = existing_doc + '_r%s.pdf' % remaining_revision
        self.assertContains(response, t)
        self.assertContains(response, t_existing)
        delete_url = reverse('mdtui-edit-delete', kwargs={'code': existing_doc})
        response = self.client.post(delete_url, {'revision': deleting_revision})
        # Redirects to search after delete and search results are updated
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertNotContains(response, t)
        self.assertContains(response, t_existing)

    def test_92_wrong_mdts_after_return_from_search(self):
        """Refs #1025 Docidx_2EmployeeResults (Wrong MDTs after return from certain state of edit_indexes views)
        Refs #1222 Indexes not saved after printing barcode
        """
        proper_mdt_name = 'Mdt5'
        improper_mdt_name = 'Mdt2'
        search_found_docs = [
            self.edit_document_name_1,
            self.edit_document_name_2,
            self.edit_document_name_3,
            self.edit_document_name_5,
            self.edit_document_name_7,

        ]
        working_doc = self.edit_document_name_2
        url = reverse('mdtui-search')
        response = self.client.post(url, self.select_mdt5)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee')
        # Posting ADL docs range
        response = self.client.post(new_url, self.date_range_all_ADL)
        self.assertEqual(response.status_code, 302)
        results_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, 200)
        for d in search_found_docs:
            self.assertContains(response, d)
        edit_url = reverse('mdtui-edit', kwargs={'code': working_doc})
        response = self.client.get(edit_url)
        self.assertContains(response, self.m2_doc1_dict['description'])  # doc parsed and rendered
        # Emulating cancel press (Going back to search)
        response = self.client.get(results_url)
        self.assertContains(response, proper_mdt_name)
        self.assertNotContains(response, improper_mdt_name)

    def test_93_barcoding_and_0_file_revisions_dms_support(self):
        """Refs #970 Test barcode generation
        Refs #735 MUI: Placeholder Document for barcoded documents

        Loosing requirement to fake 0 revisions document and adding it's support properly
        So we can now have Document with 0 revisions and 'only_metadata' created and stored
        No need to store at least 1 revision with stub document now.
        View document works this way of showing 'stub_document' instead.
        """
        url = reverse('mdtui-view-object', kwargs={'code': self.doc4})
        response = self.client.get(url)
        self.assertNotContains(response, 'stub_document.pdf')

        docrule = self.test_mdt_docrule_id
        # HACK: docrule sequence fixup.
        rule = DocumentTypeRule.objects.get(pk=docrule)
        rule.sequence_last = 3
        rule.save()
        # Going to index a doc
        url = reverse('mdtui-index-type')
        response = self.client.post(url, {docrule: 'docrule'})
        self.assertEqual(response.status_code, 302)
        # Getting indexes form and matching form Indexing Form fields names
        url = reverse('mdtui-index-details')
        response = self.client.get(url)
        rows_dict = self._read_indexes_form(response)
        post_dict = self._convert_doc_to_post_dict(rows_dict, self.doc4_barcode_dict)
        # Adding Document Indexes
        response = self.client.post(url, post_dict)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-index-source')
        response = self.client.get(url)
        self.assertContains(response, 'Friends ID: 123')
        self.assertEqual(response.status_code, 200)
        # Make the file upload
        data = {'barcoded': u'', 'printed': 'printed'}
        response = self.client.post(url+'?barcoded', data)
        # Check post returns 200
        self.assertEqual(response.status_code, 200)
        new_url = reverse('mdtui-index-finished')
        response = self.client.get(new_url)
        self.assertContains(response, self.indexing_done_string)
        self.assertContains(response, 'Friends Name: Andrew')
        self.assertContains(response, 'Additional: Something for 4')
        self.assertContains(response, 'Start Again')

        # Testing this doc exists in search results now
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Searching by Document 1,2,3 date range
        data = self.all_docs_range
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # 2 documents (one of them 'only_metadata' document) found
        # and 2 first docs are not shown because they are modified by indexing
        self.assertNotContains(response, self.doc1)
        self.assertNotContains(response, self.doc1_dict['description'])
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc2_dict['description'])
        self.assertContains(response, self.doc3)
        self.assertContains(response, self.doc3_dict['description'])
        self.assertContains(response, self.doc4)
        self.assertContains(response, self.doc4_barcode_dict['description'])

        # Testing we can view stub document now
        url = reverse('mdtui-view-object', kwargs={'code': self.doc4})
        response = self.client.get(url)
        self.assertContains(response, 'stub_document.pdf')

    def test_94_search_filters_by_doctype_properly(self):
        """Refs #1212 Search by Document type in production does not actually filter by document type

        Search results may contain a document with another document type rather then filtered by at search step 1"""
        date_range_with_keys_doc1 = {
            "Additional": "Something for 3",
        }
        doc2 = self.edit_document_name_2
        # BBB-0001 keys modifications to contain same key as ADL-0003
        doc_2_modifications = {
            "Employee": "Vovan Patsan",
            "Report Type": "Reconciliation",
            "Reporting Entity": "JTG",
            "Additional": "Something for 3",  # Same as ADL-0003
            "Report Date": "2012-04-02T00:00:00Z"
        }
        # Forcing doc2 to contain key from another doc type
        doc2_couchdoc = CouchDocument.get(docid=doc2)
        doc2_couchdoc.mdt_indexes = doc_2_modifications
        doc2_couchdoc.save()
        # Setting DocTypeRule
        url = reverse('mdtui-search-type')
        data = {'docrule': self.test_mdt_docrule_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('mdtui-search-options')
        # Getting required indexes id's
        response = self.client.get(url)
        ids = self._read_indexes_form(response)
        data = self._create_search_dict_for_range_and_keys(
            date_range_with_keys_doc1,
            ids,
            self.all_docs_range,
        )
        # Searching date range with unique doc1 keys
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # No errors appeared
        self.assertNotContains(response, "You have not defined Document Searching Options")
        # none of 2 other documents for doc type 2 present in response
        self.assertNotContains(response, self.doc2)
        self.assertNotContains(response, self.doc1)
        # Document from another doc type not present in response
        self.assertNotContains(response, self.edit_document_name_2)
        # Contains document it should in response (Should be only this doc at this stage)
        self.assertContains(response, self.doc3)

        # Search by date only
        url = reverse('mdtui-search-options')
        # Searching date range for all docs (no doc2 must be present)
        response = self.client.post(url, self.all_docs_range)
        self.assertEqual(response.status_code, 302)
        new_url = self._retrieve_redirect_response_url(response)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        # Document from another doc type not present in response
        self.assertNotContains(response, self.edit_document_name_2)
        # Contains document it should in response (Should be only this doc at this stage)
        self.assertContains(response, self.doc3)
        # We dont care about another docs here

    def test_z_cleanup(self):
        """
        Cleaning up after all tests finished.

        Must be ran after all tests in this test suite.
        """
        cleanup_docs_list = [
            self.doc1,
            self.doc2,
            self.doc3,
            self.doc4,
            self.edit_document_name_2,
            self.edit_document_name_3,
            self.edit_document_name_5,
            self.edit_document_name_7,
            self.edit_document_name_1,
            'TST00000001',
            'TST00000002'
        ]
        # Deleting all test MDT's
        # (with doccode from var "test_mdt_docrule_id" and "test_mdt_docrule_id2")
        # using MDT's API.
        url = reverse('api_mdt')
        docrules_list = [
            self.test_mdt_docrule_id,
            self.test_mdt_docrule_id2,
            self.test_mdt_docrule_id3,
            self.test_mdt_docrule_id4
        ]
        for mdt_ in docrules_list:
            response = self.client.get(url, {"docrule_id": str(mdt_)})
            data = json.loads(str(response.content))
            for key, value in data.iteritems():
                mdt_id = data[key]["mdt_id"]
                response = self.client.delete(url, {"mdt_id": mdt_id})
                self.assertEqual(response.status_code, 204)

        # Deleting all docs used in tests
        for argument in cleanup_docs_list:
            url = reverse('api_file', kwargs={'code': argument})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)

        if settings.COUCHDB_COMPACT:  # (default is False, override in local_settings.py)
            # Compacting CouchDB dmscouch/mdtcouch DB's after tests
            print 'Compacting CouchDB'
            server = Server()
            db1 = server.get_or_create_db(self.couchdb_name)
            db1.compact()
            db2 = server.get_or_create_db(self.couchdb_mdts_name)
            db2.compact()
