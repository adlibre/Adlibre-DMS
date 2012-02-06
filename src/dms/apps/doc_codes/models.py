"""
Module: DocCodes Model for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django.db import models
import re

DOCCODE_TYPES = [
    ('1', 'Default'),
    ('2', 'Credit Card'),
]

class DoccodeModel(models.Model):
    """
    Main Model for Doccodes.
    In order for an app to function Properly must contain:
    Basic model for storing "No doccode" Documents.
        - doccode_id = 1000 (or any no_doccode Id set)
        - no_doccode = True
        - active = True
        - regex = '' (no filename data)

    Maybe we need to add function to check and store this model on init.
    For now DMR requires it to be like so.
    """
    doccode_type = models.CharField(choices = DOCCODE_TYPES, max_length = 64, default = '1')
    doccode_id = models.IntegerField('Doccode ID')
    no_doccode = models.BooleanField(default = False)
    title = models.CharField("Doccode Name", max_length=60)
    description = models.TextField("Description", blank=True)
    regex = models.CharField("Filename Regex", max_length=100, blank=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u'Doccode:' + unicode(self.get_title())

    def validate(self, document_name):
        """
        Validates doccode against available "document_name" string.
        Returns True if OK and False if not passed.
        """

        # TODO: expansion to validate document_name against "is_luhn_valid(self, cc)" for document_type:2 (credit Card)
        regex = '^' + self.regex + '$'
        if self.regex == '' and re.match(regex, document_name) and self.no_doccode:
            return True
        if not self.no_doccode and re.match(regex, document_name):
            return True
        return False

    def split(self, document_name=''):
        """
        Method to generate folder hierarchy to search for document depending on name.
        Returns spliting method List:
        Usage e.g.:
        File name:  abcde222.pdf (document_name = 'abcde222')
        Spliting method:  ['abcde', '222', 'abcde222']
        In case of doccode == no_doccode returns current DATE
        """
        if self.no_doccode or not document_name:
            # no Doccode spliting method
            return ['{{DATE}}']
        else:
            # TODO: KLUDGE: Here split methods are simply listed below to finish refactoring. NEEDS elegant method.
            if self.doccode_id == 2:
                d = [ document_name[0:3], document_name[4:8], document_name]
            if self.doccode_id == 5:
                d = [ document_name[0:4], document_name[5:9], document_name[10:13], document_name[14:18], document_name ]
            if self.doccode_id == 4:
                d = [ document_name[0:4], document_name[5:7], document_name[8:10], document_name[11:20], document_name]
            if self.doccode_id == 3:
                # Split document_name as per Project Gutenberg method for 'eBook number' not, eText
                # http://www.gutenberg.org/dirs/00README.TXT
                d = []
                for i in range(len(document_name)):
                    d.append(document_name[i-1:i])
                d.append(document_name)
            if self.doccode_id == 1:
                d = [ document_name[0:5], document_name[5:8], document_name]
            if not d:
                d='Storage_errors' #folder name for improper doccdes!!!!!
            #print "Spliting method: ", d
            return d

    def is_luhn_valid(self, cc):
        """
        Method to validate Lughn algorithm based on:
        # Credit: http://en.wikipedia.org/wiki/Luhn_algorithm
        """
        num = [int(x) for x in str(cc)]
        return sum(num[::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0

    def get_id(self):
        #print 'Doccode model "get_id" called.'
        return self.doccode_id

    def get_title(self):
        title = getattr(self, 'title', '')
#        if not title:
#            title = getattr(self, 'name', '')
        return title

    def get_directory_name(self):
        return str(self.get_id())