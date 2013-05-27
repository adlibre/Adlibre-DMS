"""
Module: DMS Core tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

import os
import datetime
import zlib
import hashlib
import json

from couchdbkit import Server

from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from adlibre.dms.base_test import DMSTestCase

from document_processor import DocumentProcessor
from dms_plugins.models import DocTags


class CoreTestCase(DMSTestCase):
    """Data for testing Core specific workflows"""

    def __init__(self, *args, **kwargs):
        """Per test suite initialisation"""
        super(CoreTestCase, self).__init__(*args, **kwargs)

        self.couchdb_name = 'dmscouch_test'

        self.admin_user = User.objects.filter(is_superuser=True)[0]

        self.fs_metadata_ext = 'json'

        self.doc1 = {
            'description': u'Additional Secondary Indexes Data for file ADL-1111',
            'date': u'15/05/2013',
            u'Friends ID': u'123456',
            u'Friends Name': u'Yuri',
            u'Required Date': u'15/05/2013',
            u'Employee ID': u'11111',
            u'Employee Name': u'Yuri',
            u'Additional': u'Something more',
        }

    def _get_fixtures_file(self, code, extension='pdf'):
        """Opens a file from DMS fixtures directory"""
        path = os.path.join(self.test_document_files_dir, code + '.' + extension)
        result_file = open(path, 'r')
        result_file.seek(0)
        return result_file

    def _chek_documents_dir(self, filename, docrule, code=False, check_exists=True):
        """Tests DMS documents folder (Local Storage) for existing of given file there

        @filename should be like 'ADL-0001.json' or 'ADL-0002'
        @docrule is an instance of document's DocumentTypeRule()
        @check_exists is a task to test if this file exists in file system
        @code is a certain code specified for this filename (need in case it is impossible to get from @filename)
        """
        docs_dir = settings.DOCUMENT_ROOT
        file_path_list = docrule.split(filename)
        check_path = os.path.join(docs_dir, str(docrule.pk))
        if not code:
            # Obtaining code from filename
            file_path_list[-1] = filename.split('.')[0]
        else:
            file_path_list[-1] = code
        for item in file_path_list:
            check_path = os.path.join(check_path, item)
        check_path = os.path.join(check_path, filename)
        if check_exists:
            if not os.path.isfile(check_path):
                raise AssertionError('No such file: %s' % check_path)
        return check_path

    def _check_files_equal(self, fixtures_file, dms_file, compressed=True, check=True):
        """Tests if 2 given file objects are equal. Taking compression into account

        @fixtures_file is open file instance
        @dms_file is open file instance
        @compressed is a switch to compress @fixtures_file before comparing hashes
        """
        def get_hash(document, method='md5', salt=settings.SECRET_KEY):
            h = hashlib.new(method)
            h.update(document)
            h.update(salt)
            return h.hexdigest()
        if compressed:
            f_file = zlib.compress(fixtures_file.read())
            fixt_hashcode = get_hash(f_file)
        else:
            fixt_hashcode = get_hash(fixtures_file.read())
        dms_string = dms_file.read()
        dms_hashcode = get_hash(dms_string)
        if check:
            self.assertEqual(fixt_hashcode, dms_hashcode)
        return fixt_hashcode, dms_hashcode

    def _remove_file(self, code, extension='pdf', check_couchdb=True, check_revision_1=True):
        """Removes a file from DMS

        @code is an assigned object code
        """
        processor = DocumentProcessor()
        doc = processor.read(code, {'user': self.admin_user})
        processor = DocumentProcessor()
        processor.delete(code, {'user': self.admin_user})
        if processor.errors:
            raise AssertionError('Removing document error: %s' % processor.errors)
        if check_revision_1:
            r1 = code + '_r1.' + extension
            check_path = self._chek_documents_dir(r1, doc.get_docrule(), code=code, check_exists=False)
            if os.path.isfile(check_path):
                raise AssertionError('File: %s has not been actually removed' % code)
        rev_data = code + '.' + self.fs_metadata_ext
        check_metadata_path2 = self._chek_documents_dir(rev_data, doc.get_docrule(), code=code, check_exists=False)
        if os.path.isfile(check_metadata_path2):
            raise AssertionError('File: %s has not been actually removed' % check_metadata_path2)
        if check_couchdb:
            couchfile = self._open_couchdoc(self.couchdb_name, code)
            if couchfile:
                print couchfile
                print 'CouchDB file contents: \n'
                for key, value in couchfile.iteritems():
                    print '%s: %s' % (key, value)
                all_couchdocs = self._list_couchdocs(self.couchdb_name)
                print all_couchdocs
                raise AssertionError('CouchDB document has not been removed: %s' % code)

    def _open_couchdoc(self, db_name, code, view_name='_all_docs'):
        """Open given document in a given CouchDB database

        @db_name is a couchdb name to look in for doc
        @code is a CouchDB document _id
        @view_name is a non default (_all_docs) name of CouchDB view to look for code
        """
        firstdoc = {}
        server = Server()
        db = server.get_or_create_db(db_name)
        r = db.view(
            view_name,
            key=code,
            include_docs=True,
        )
        for row in r:
            firstdoc = row['doc']
        return firstdoc

    def _list_couchdocs(self,  db_name):
        """Downloads all the documents that are currently in CouchDB now"""
        docs = {}
        server = Server()
        db = server.get_or_create_db(db_name)
        r = db.view(
            'dmscouch/all',
            include_docs=True,
        )
        for row in r:
            docs[row['doc']['_id']] = row['doc']
        return docs



class DocumentProcessorTest(CoreTestCase):
    """Test for core.DocumentProcessor() and it's workflow"""

    def setUp(self):
        """Per test initialization"""
        self.processor = DocumentProcessor()

    def test_00_initial_one_time_setup(self):
        """Populating data into test space"""
        pass

    def test_01_basic_create(self):
        """Create workflow with bulk file feeding,
        e.g. upload file without any additional data, named according to DMS rules.
        Should be file ADL-0001.pdf

        Tests it creates ADL-0001.json
        Tests it creates ADL-0001_r1.pdf
        Tests it does not create revision 2 or related files.
        Tests if file is compressed and stored into proper place with hashes
        Tests document created in CouchDB
        """
        self._list_couchdocs(self.couchdb_name)
        filecode = self.documents_pdf[0]
        test_file = self._get_fixtures_file(filecode)
        doc = self.processor.create(test_file, {'user': self.admin_user})
        # Processor has no errors
        if self.processor.errors:
            raise AssertionError([e for e in self.processor.errors])
        # Proper name
        self.assertEqual(doc.get_filename(), filecode + '.pdf')
        # Proper docrule
        self.assertEqual(doc.get_docrule().pk, 2)
        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        if not 1 in file_rev_data.keys():
            raise AssertionError('No revision data for revision 1 generated by manager')
        if 2 in file_rev_data.keys():
            raise AssertionError('Should not contain revision 2 at this stage of testing')
        rev1 = file_rev_data[1]
        self.assertIn('compression_type', rev1)
        self.assertEqual(rev1['compression_type'], 'GZIP')
        self.assertIn('created_date', rev1)
        try:
            datetime.datetime.strptime(rev1['created_date'], settings.DATETIME_FORMAT)
        except Exception, e:
            raise AssertionError('Revision 1 datetime is wrong with error: %s' % e)
        self.assertIn('mimetype', rev1)
        self.assertEqual(rev1['mimetype'], 'application/pdf')
        self.assertIn('name', rev1)
        self.assertEqual(rev1['name'], filecode + '_r1.pdf')
        self.assertIn('revision', rev1)
        self.assertEqual(rev1['revision'], 1)
        # Files created
        json_path = self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        path1 = self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode)
        path = self._chek_documents_dir(filecode + '_r2.pdf', doc.get_docrule(), code=filecode, check_exists=False)
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        # Proper files in proper places with proper data
        self._check_files_equal(self._get_fixtures_file(filecode), open(path1, 'r'))
        hcode1, hcode2 = self._check_files_equal(self._get_fixtures_file(filecode), open(json_path, 'r'), check=False)
        if hcode1 == hcode2:
            raise AssertionError('Wrong data stored into json file.')
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, filecode)
        self.assertEqual(couchdoc['id'], filecode)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')

    def test_02_create_existing_code(self):
        """Feeding existing file again and checking for errors and actions

        e.g. Create file ADL-0001 with file ADL-0001 already existing in system form previous tests
        """
        filecode = self.documents_pdf[0]
        test_file = self._get_fixtures_file(filecode)
        doc = self.processor.create(test_file, {'user': self.admin_user})
        if self.processor.errors:
            self.assertIn('409', str(self.processor.errors[0]))
        else:
            raise AssertionError('Processor does not indicate about "create" of existing file.')
        path = self._chek_documents_dir(filecode + '_r2.pdf', doc.get_docrule(), code=filecode, check_exists=False)
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        json_path = self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        json_data = open(json_path).read()
        rev_data = json.loads(json_data)
        if '2' in rev_data.iterkeys() or 2 in rev_data.iterkeys():
            raise AssertionError('Revisions integrity broken. Revision 2 metadata created, but it should not be so.')

    def test_03_create_new_code(self):
        """Creating new code uploading the same file (rename file upon creation)

        e.g. Uploading a file ADL-0001.pdf with forcing code ADL-0002 assignment.
        """
        filecode = self.documents_pdf[1]
        filename = self.documents_pdf[0]
        test_file = self._get_fixtures_file(filename)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'barcode': filecode})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        # Only revision 1 and metadata present
        json_path = self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        path1 = self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode)
        path2 = self._chek_documents_dir(filecode + '_r2.pdf', doc.get_docrule(), code=filecode, check_exists=False)
        if os.path.isfile(path2):
            raise AssertionError('Revision 2 file should be absent')
        # Proper files in proper places with proper data
        self._check_files_equal(self._get_fixtures_file(filename), open(path1, 'r'))
        hcode1, hcode2 = self._check_files_equal(self._get_fixtures_file(filename), open(json_path, 'r'), check=False)
        if hcode1 == hcode2:
            raise AssertionError('Wrong data stored into json file.')
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, filecode)
        self.assertEqual(couchdoc['id'], filecode)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')

    def test_04_create_file_with_indexes(self):
        """Create a file with certain code and secondary indexes specified

        e.g. Using a given 'index_info' dict in MUI
        """
        filecode = self.documents_pdf[2]
        filename = self.documents_pdf[0]
        tests_file = self._get_fixtures_file(filename)
        index_info = self.doc1
        # FIXME: this should not happen. Original dict given to plugin is modified.
        description = index_info['description']
        options = {
            'user': self.admin_user,
            'barcode': filecode,
            'index_info': index_info,
        }
        doc = self.processor.create(tests_file, options)
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode)
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, filecode)
        self.assertEqual(couchdoc['id'], filecode)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')
        if couchdoc['index_revisions']:
            raise AssertionError('File should not contain index revisions at this stage.')
        if not couchdoc['metadata_description'] == description:
            raise AssertionError('description metadata broken')
        if not '1' in couchdoc['revisions']:
            raise AssertionError('File indexing data not stored to CouchDB')
        for index in index_info.iterkeys():
            if not index in couchdoc['mdt_indexes'] and not index in ['description', 'date']:
                raise AssertionError('Secondary index absent: %s' % index)

    def test_05_create_0_revisions_file(self):
        """Create a file storing only metadata and 0 file revisions

        This creation should produce CpuchDB document without storing any files,
        but reserving this code, indicating this file exists.
        """
        filecode = self.documents_pdf[3]
        index_info = self.doc1
        options = {
            'user': self.admin_user,
            'barcode': filecode,
            'index_info': index_info,
            'only_metadata': True,
        }
        doc = self.processor.create(None, options)
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        json_path = self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule(), check_exists=False)
        rev1_path = self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode, check_exists=False)
        if os.path.isfile(json_path) or os.path.isfile(rev1_path):
            raise AssertionError('Directory should not contain files on creating 0 revisions file')
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, filecode)
        self.assertEqual(couchdoc['id'], filecode)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')

    def test_06_create_document_without_security_permission(self):
        """Create a file request for user that is not in security group"""
        filecode = self.documents_pdf[4]
        tests_file = self._get_fixtures_file(filecode)
        user = User.objects.create_user(username='someone')
        doc = self.processor.create(tests_file, {'user': user, 'barcode': filecode})
        if not self.processor.errors:
            raise AssertionError('Processor should fail creating file for user not in security group')
        json_path = self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule(), check_exists=False)
        rev1_path = self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode, check_exists=False)
        if os.path.isfile(json_path) or os.path.isfile(rev1_path):
            raise AssertionError('Directory should not contain files on creating code without security permission')
        # Couchdb doc is not created
        couchdoc = self._open_couchdoc(self.couchdb_name, filecode)
        if couchdoc:
            raise AssertionError('CouchDB should not contain document: %s' % filecode)

    def test_07_create_by_user_in_security_group(self):
        """Create a file for user that is in security group"""
        user_login = 'some_user'
        user_pass = 'something'
        # give user a group 'security' (permission)
        user = User.objects.create_user(username=user_login, password=user_pass)
        group = Group.objects.get(name='security')
        group.user_set.add(user)
        # Upload a doc again
        filecode = self.documents_pdf[4]
        tests_file = self._get_fixtures_file(filecode)
        doc = self.processor.create(tests_file, {'user': user, 'barcode': filecode})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        # Only revision 1 and metadata present
        self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode)
        path2 = self._chek_documents_dir(filecode + '_r2.pdf', doc.get_docrule(), code=filecode, check_exists=False)
        if os.path.isfile(path2):
            raise AssertionError('Revision 2 file should be absent')
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, filecode)
        self.assertEqual(couchdoc['id'], filecode)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '2')

    def test_08_no_code_creation(self):
        """Create a code that has no Document Type Rule set"""
        filecode = self.no_docrule_files[0]
        tests_file = self._get_fixtures_file(filecode, extension='jpg')
        doc = self.processor.create(tests_file, {'user': self.admin_user})
        if doc is not None:
            raise AssertionError('Assume we have to return None not a doc instance in case of creation no docrule file')
        if not self.processor.errors:
            raise AssertionError('Processor should contain errors')
        if self.processor.errors != [u'No document type rule found for file Z50141104.jpg']:
            raise AssertionError('Processor errors are wrong.')

    def test_09_no_code_creation_with_barcode_set(self):
        """Create a code that has no Document Type Rule set"""
        filecode = self.no_docrule_files[0]
        tests_file = self._get_fixtures_file(filecode, extension='jpg')
        doc = self.processor.create(tests_file, {'user': self.admin_user, 'barcode': filecode})
        print doc
        if doc is not None:
            raise AssertionError('Assume we have to return None not a doc instance in case of creation no docrule file')
        if not self.processor.errors:
            raise AssertionError('Processor should contain errors')

    def test_10_create_jpg(self):
        """Create a JPG file"""
        filecode = self.documents_jpg[2]
        test_file = self._get_fixtures_file(filecode, extension='jpg')
        doc = self.processor.create(test_file, {'user': self.admin_user})
        # Processor has no errors
        if self.processor.errors:
            raise AssertionError(self.processor.errors[0])
        # Proper name
        self.assertEqual(doc.get_filename(), filecode + '.jpg')
        # Proper docrule
        self.assertEqual(doc.get_docrule().pk, 9)
        # Proper revision data generated and has all the indexes required
        file_rev_data = doc.get_file_revisions_data()
        if not 1 in file_rev_data.keys():
            raise AssertionError('No revision data for revision 1 generated by manager')
        if 2 in file_rev_data.keys():
            raise AssertionError('Should not contain revision 2 at this stage of testing')
        rev1 = file_rev_data[1]
        self.assertIn('compression_type', rev1)
        self.assertEqual(rev1['compression_type'], 'GZIP')
        self.assertIn('created_date', rev1)
        try:
            datetime.datetime.strptime(rev1['created_date'], settings.DATETIME_FORMAT)
        except Exception, e:
            raise AssertionError('Revision 1 datetime is wrong with error: %s' % e)
        self.assertIn('mimetype', rev1)
        self.assertEqual(rev1['mimetype'], 'image/jpeg')
        self.assertIn('name', rev1)
        self.assertEqual(rev1['name'], filecode + '_r1.jpg')
        self.assertIn('revision', rev1)
        self.assertEqual(rev1['revision'], 1)
        # Files created
        json_path = self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        path1 = self._chek_documents_dir(filecode + '_r1.jpg', doc.get_docrule(), code=filecode)
        path = self._chek_documents_dir(filecode + '_r2.jpg', doc.get_docrule(), code=filecode, check_exists=False)
        if os.path.isfile(path):
            raise AssertionError('Revision 2 file should be absent')
        # Proper files in proper places with proper data
        self._check_files_equal(self._get_fixtures_file(filecode, extension='jpg'), open(path1, 'r'))
        hcode1, hcode2 = self._check_files_equal(self._get_fixtures_file(filecode, extension='jpg'), open(json_path, 'r'), check=False)
        if hcode1 == hcode2:
            raise AssertionError('Wrong data stored into json file.')
        # Couchdb doc created properly
        couchdoc = self._open_couchdoc(self.couchdb_name, filecode)
        self.assertEqual(couchdoc['id'], filecode)
        self.assertEqual(couchdoc['metadata_doc_type_rule_id'], '9')

    def test_11_create_tags(self):
        """Create a document with Tags. Stored into SQL DB"""
        tagstring = 'some_tag'
        filecode = self.documents_hash[0][0]
        test_file = self._get_fixtures_file(filecode)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'tag_string': tagstring})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode)
        self.assertEqual(doc.get_tag_string(), tagstring)
        # Deleting doc and checking tags deleted too.
        self._list_couchdocs(self.couchdb_name)
        self._remove_file(filecode)
        try:
            tags = DocTags.objects.get(name=filecode)
            raise AssertionError('Tags for document %s should be deleted' % filecode)
        except ObjectDoesNotExist:
            pass

    def test_12_create_with_hashcode(self):
        """Creating a file with new code with hashcode validation for provided file"""
        # TODO: logic here is broken somewhere. I should fix it.
        # @dms_stored_hashcode should not be different
        filecode = self.documents_hash[1][0]
        hcode = self.documents_hash[1][1]
        dms_stored_hashcode = '479610f78adc3aa7d30ea1e9fb166761'
        test_file = self._get_fixtures_file(filecode)
        doc = self.processor.create(test_file, {'user': self.admin_user, 'hashcode': hcode})
        if self.processor.errors:
            raise AssertionError('Processor create failed with errors: %s' % self.processor.errors)
        if not 'hashcode' in doc.get_file_revisions_data()[1]:
            raise AssertionError('Hash code is not present')
        f = self.processor.read(filecode, {'user': self.admin_user, 'hashcode': hcode})
        self.assertEqual(doc.get_file_revisions_data()[1]['hashcode'], dms_stored_hashcode)
        self.assertEqual(f.get_hashcode(), hcode)
        json_path = self._chek_documents_dir(filecode + '.' + self.fs_metadata_ext, doc.get_docrule())
        self._chek_documents_dir(filecode + '_r1.pdf', doc.get_docrule(), code=filecode)
        json_file = json.load(open(json_path))
        self.assertIn('hashcode', json_file['1'])
        self.assertEqual(json_file['1']['hashcode'], dms_stored_hashcode)
        pass

    def test_13_basic_read(self):
        """Read a document from DMS"""
        # TODO: develop
        # filecode = self.documents_pdf[0]
        # doc = self.processor.read(filecode, {'user': self.admin_user})
        # print doc

    def test_14_read_no_docrule(self):
        # TODO: develop
        pass

    def test_15_read_only_metadata(self):
        # TODO: develop
        pass

    def test_16_read_not_existing(self):
        # TODO: develop
        pass

    def test_zz_cleanup(self):
        """Cleaning alll the docs and data that are touched or used in those tests"""
        for code in self.documents_pdf:
            self._remove_file(code)
        for code in [self.documents_hash[1][0], ]:
            self._remove_file(code)
        for code in [self.documents_jpg[2], ]:
            self._remove_file(code, extension='jpg')

    # TODO: check tags deleted after deleting correspondent doc (self.documents_hash[0])

