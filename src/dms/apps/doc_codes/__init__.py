"""
Module: DocCodes for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""
from models import DoccodeModel
#
#class Doccode(object):
#    no_doccode = False
#
#    def get_id(self):
#        return self.doccode_id
#
#    def get_title(self):
#        title = getattr(self, 'title', '')
#        if not title:
#            title = getattr(self, 'name', '')
#        return title
#
#    def get_directory_name(self):
#        return str(self.get_id())

#class NoDoccode(Doccode):
#    title = 'No doccode'
#    description = 'This doccode is assigned to the files that have no other suitable doccode.'
#    active = True
#    doccode_id = 1000
#    no_doccode = True
#
#    def validate(self, document_name):
#        return True
#
#    def split(self):
#        return ['{{DATE}}']

class DoccodeManager(object):
    def __init__(self):
        self.doccodes = DoccodeModel.objects.all()

#    def register(self, doccode):
#        self.doccodes[doccode.get_id()] = doccode

    def find_for_string(self, string):
        res = DoccodeModel.objects.filter(no_doccode = True, active = True)[0]
        for doccode in self.doccodes:
            #print "%s is validated by %s: %s" % (string, doccode, doccode.validate(string))
            if doccode.validate(string):
                res = doccode
                break
        return res

    def get_doccodes(self):
        return DoccodeModel.objects.all()

    def get_doccode_by_name(self, name):
        doccodes = self.get_doccodes()
        try:
            doccode = doccodes.filter(title=name)[0]
            return doccode
        except: pass
        for doccode in doccodes:
            if doccode.get_title() == name:
                return doccode
        return None

DoccodeManagerInstance = DoccodeManager()

#DoccodeManagerInstance.register(NoDoccode())

# FIXME: These should automatically load when a new class is created / file saved in this plugin directory.

#from test_pdf import TestPDFDoccode
#DoccodeManagerInstance.register(TestPDFDoccode())
#
#from adlibre_invoices import AdlibreInvoicesDoccode
#DoccodeManagerInstance.register(AdlibreInvoicesDoccode())
#
#from project_gutenberg_ebooks import ProjectGutenbergEbooksDoccode
#DoccodeManagerInstance.register(ProjectGutenbergEbooksDoccode())
#
#from fax_tiff import FaxTiffDoccode
#DoccodeManagerInstance.register(FaxTiffDoccode())
#
#from credit_card import CreditCardDoccode
#DoccodeManagerInstance.register(CreditCardDoccode())


