class DoccodeManager(object):
    def __init__(self):
        self.doccodes = {}

    def register(self, doccode):
        self.doccodes[doccode.get_id()] = doccode

    def find_for_string(self, string):
        res = None
        #print "ALL DOCCODES: %s" % self.get_doccodes() #TODO: log.debug this
        for doccode in self.get_doccodes().values():
            if doccode.validate(string):
                res = doccode
                break
        return res

    def get_doccodes(self):
        return self.doccodes

DoccodeManagerInstance = DoccodeManager()

from adlibre_invoices import AdlibreInvoicesDoccode
DoccodeManagerInstance.register(AdlibreInvoicesDoccode())

from test_pdf import TestPDFDoccode
DoccodeManagerInstance.register(TestPDFDoccode())