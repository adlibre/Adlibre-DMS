


import json
from django.test import TestCase
from django.core.urlresolvers import reverse
import re

# auth user
username = 'admin'
password = 'admin'

test_mdt_docrule_id = 2

class MDTUI(TestCase):
    def setUp(self):
        # We-re using only logged in client in this test
        self.client.login(username=username, password=password)

    def test_opens_app(self):
        url = reverse('mdtui-home')
        response = self.client.get(url)
        self.assertContains(response, 'To continue, choose from the options below')
        self.assertEqual(response.status_code, 200)

    def test_step1(self):
        url = reverse('mdtui-index')
        response = self.client.get(url)
        self.assertContains(response, '<legend>Step 1: Select Document Type</legend>')
        self.assertContains(response, 'Adlibre Invoices')
        self.assertEqual(response.status_code, 200)
    
    def test_step1_post_redirect(self):
        url = reverse('mdtui-index')
        response = self.client.post(url, {'docrule': test_mdt_docrule_id})
        self.assertEqual(response.status_code, 302)

        #getting redirect url by regexp expression
        new_url = re.search("(?P<url>https?://[^\s]+)", str(response)).group("url")
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label class="control-label">Description</label>')
        self.assertContains(response, 'Creation Date')
