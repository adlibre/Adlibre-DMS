"""
Module: Document Type Rules Model Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

import magic

from django.conf import settings
from django.core.urlresolvers import reverse

from base_test import AdlibreTestCase
from django.test import TestCase


from doc_codes.models import DocumentTypeRule

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


class CoreModelTest(TestCase):
    "Test the models contained in the models."
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
            self.assertEquals(obj.add_new_document(), result)
            self.assertEquals(obj.get_last_document_number(), 1001)
