import json
from django.test import TestCase
from django.core.urlresolvers import reverse

# auth user
username = 'admin'
password = 'admin'

api = 'http://127.0.0.1:8000/api/mdt/'
template = {
    "docrule_id": "1",
    "description": "<-- description of this metadata template -->",
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

class MetadataCouchDB(TestCase):
    def setUp(self):
        # We-re using only logged in client in this test
        self.client.login(username=username, password=password)

    def test_mdt_adding(self):
        """
        Posts Example MDT's to CouchDB through API
        Does test sending Metadata Template through API
        """
        mdt = json.dumps(template)

        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": mdt})
        self.assertContains(response, "ok")
        self.assertEqual(response.status_code, 200)


