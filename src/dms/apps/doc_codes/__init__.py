class DoccodeManager(object):
    def __init__(self):
        self.doccodes = {}

    def register(self, doccode):
        self.doccodes[doccode.get_id()] = doccode

    def find_for_string(self, string):
        res = None
        print "ALL DOCCODES: %s" % self.doccodes
        for doccode in self.doccodes.values():
            if doccode.validate(string):
                res = doccode
                break
        return res

DoccodeManagerInstance = DoccodeManager()

from adlibre_invoices import AdlibreInvoicesDoccode
DoccodeManagerInstance.register(AdlibreInvoicesDoccode())

from test_pdf import TestPDFDoccode
DoccodeManagerInstance.register(TestPDFDoccode())