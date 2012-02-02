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
    ('1', 'Document'),
    ('2', 'Credit Card'),
    ('3', 'Other')
]

class DoccodeModel(models.Model):
    doccode_id = models.IntegerField('Doccode ID')
    no_doccode = models.BooleanField(default = False)
    title = models.CharField("Doccode Name", max_length=60)
    description = models.TextField("Description", blank=True)
    regex = models.CharField("Filename Regex", max_length=100, blank=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u'Doccode:' + unicode(self.get_title())

    def validate(self, document_name):
        regex = '^' + self.regex + '$'
        if not self.no_doccode and re.match(regex, document_name):
            return True
        return False

    def split(self, document_name):
        if self.no_doccode:
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
                d='needs_refactor' #folder name for new doccdes!!!!!
            return d

    # Credit: http://en.wikipedia.org/wiki/Luhn_algorithm
    def is_luhn_valid(self, cc):
        num = [int(x) for x in str(cc)]
        return sum(num[::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0

    def get_id(self):
        return self.doccode_id

    def get_title(self):
        title = getattr(self, 'name', '')
        if not title:
            title = getattr(self, 'title', '')
        return title

    def get_directory_name(self):
        return str(self.get_id())