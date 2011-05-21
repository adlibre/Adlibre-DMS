import re

from doc_codes import DoccodeManagerInstance
from base import Doccode

class AdlibreInvoicesDoccode(Doccode):
    title = 'Adlibre Invoices'
    description = 'ADL-[0-9]{4}]'
    active = True
    doccode_id = 2

    def validate(self, document_name):
        if re.match('^ADL-[0-9]{4}$', document_name):
            return True
        return False

    def split(self, document_name):
        d = [ document_name[0:3], document_name[4:8], ]
        return d

