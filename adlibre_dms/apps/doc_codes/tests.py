"""
Module: Document Type Rules Model Unit Tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.test import TestCase

from doc_codes.models import DocumentTypeRule


class DocCodeModelTest(TestCase):
    """DocCode Model Tests"""
    def setUp(self):
        """Populate test database with model instances."""
        # DocCodeModelTest Test Data
        self.MODELS = [DocumentTypeRule, ]

        self.generated_barcodes = (
            #(docode_id, result)
            (1, 'UNC-1001'),
            (2, 'ADL-1001'),
            (3, False),
            (4, False),
            (5, False),
            (6, False),
            (7, 'BBB-1001'),
            (8, 'CCC-1001'),
        )

    def tearDown(self):
        """Depopulate created model instances from test database."""
        for model in self.MODELS:
            for obj in model.objects.all():
                obj.delete()

    def test_generate_document_barcode(self):
        """This is a test for barcode generation."""

        for docrule_id, result in self.generated_barcodes:
            obj = DocumentTypeRule.objects.get(pk=docrule_id)
            obj.set_last_document_number(1000)
            self.assertEquals(obj.allocate_barcode(), result)
            self.assertEquals(obj.get_last_document_number(), 1001)
