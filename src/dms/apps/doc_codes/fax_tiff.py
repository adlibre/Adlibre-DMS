import re
from doccodes import Doccode

from doc_codes import DoccodeManagerInstance
from base import Doccode

class DocCode(Doccode):
    active = True
    name = 'Fax Tiff documents'
    description = '[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{1,9}'
    doccode_id = 4

    def validate(self, document_name):
        if re.match("^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{1,9}$", document_name):
            return True
        return False

    def split(self, document_name):
        d = [ document_name[0:4], document_name[5:7], document_name[8:10], document_name[11:20]]
        return d
