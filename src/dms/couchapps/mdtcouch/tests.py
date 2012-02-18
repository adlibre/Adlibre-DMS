import urllib2
import urllib
import json

# TODO: refactor this script to normal Django tests...

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

mdt = json.dumps(template)
data = urllib.urlencode({"mdt": mdt})
request = urllib2.Request(api)
print 'Request method before data:', request.get_method()

request.add_data(data)
print 'Request method after data :', request.get_method()
request.add_header('User-agent', 'Django Tests Runner (http://www.doughellmann.com/PyMOTW/)')

print
print 'OUTGOING DATA:'
print request.get_data()

print
print 'SERVER RESPONSE:'
print urllib2.urlopen(request).read()