"""
Module: Document Type Rules Model Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

import magic

from django.conf import settings
from django.core.urlresolvers import reverse

from django.test import TestCase

from doc_codes.models import DocumentTypeRule
from document import Document


# DocCodeModelTest Test Data
MODELS = [DocumentTypeRule,]

generated_barcodes = (
    #(docode_id, result)
    (1, False),
    (2, 'ADL-1001'),
    (3, False),
    (4, False),
    (5, False),
    (1000, False),
)


class DocCodeModelTest(TestCase):
    """
    DocCode Model Tests
    """
    def setUp(self):
        'Populate test database with model instances.'

    def tearDown(self):
        'Depopulate created model instances from test database.'
        for model in MODELS:
            for obj in model.objects.all():
                obj.delete()

    def test_generate_document_barcode(self):
        "This is a test for barcode generation."

        for doccode_id, result in generated_barcodes:
            obj = DocumentTypeRule.objects.get(doccode_id=doccode_id)
            obj.set_last_document_number(1000)
            self.assertEquals(obj.allocate_barcode(), result)
            self.assertEquals(obj.get_last_document_number(), 1001)


class DocumentObjectTest(TestCase):
    """
    Document Model Tests
    (Temporarily Staged here to get around django unit test restrictions
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_doccode(self):

        doc = Document()
	# TODO: Write some tests
        #doc.doccode = 'ADL-1234'
        #print doc.get_docrule()
        #print doc
