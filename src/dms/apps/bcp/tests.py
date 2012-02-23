"""
Module: Bar Code Printer Unit Tests
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.core.urlresolvers import reverse

from base_test import AdlibreTestCase

"""
Test data
"""
# auth user
username = 'admin'
password = 'admin'

variable_length_barcode_types = ('code39',)
variable_length_barcode_codes = ('ABC1234', '123456789', 'ABC-1234')

class BarCodeTest(AdlibreTestCase):

    def test_generate_barcode(self):
        for type in variable_length_barcode_types:
            for code in variable_length_barcode_codes:
                url = reverse('bcp-generate', kwargs = {'barcode_type': type, 'code': code, })
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)