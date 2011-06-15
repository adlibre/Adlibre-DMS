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

    def get_doccode_by_name(self, name):
        for doccode in self.get_doccodes().values():
            if doccode.get_title() == name:
                return doccode
        return None

DoccodeManagerInstance = DoccodeManager()

from test_pdf import TestPDFDoccode
DoccodeManagerInstance.register(TestPDFDoccode())

from adlibre_invoices import AdlibreInvoicesDoccode
DoccodeManagerInstance.register(AdlibreInvoicesDoccode())

from project_gutenberg_ebooks import ProjectGutenbergEbooksDoccode
DoccodeManagerInstance.register(ProjectGutenbergEbooksDoccode())

from fax_tiff import FaxTiffDoccode
DoccodeManagerInstance.register(FaxTiffDoccode())

from credit_card import CreditCardDoccode
DoccodeManagerInstance.register(CreditCardDoccode())


