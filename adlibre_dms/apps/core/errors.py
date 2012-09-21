"""
Module: DMS Core error handlers.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
Desc: All core errors should be declared here.
"""

class ConfigurationError(Exception):
    pass

class DmsException(Exception):
    def __init__(self, value, code):
        self.parameter = value
        self.code = code

    def __str__(self):
        return super(DmsException, self).__str__() + (" %s - %s" % (self.code, repr(self.parameter)))

    def __repr__(self):
        return super(DmsException, self).__repr__() + (" %s - %s" % (self.code, repr(self.parameter)))

    def __unicode__(self):
        return unicode(str(self))