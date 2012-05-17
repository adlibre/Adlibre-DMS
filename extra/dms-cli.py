#!/usr/bin/env python

import sys
import os

#
# Adlibre DMS: Example of command line uploading using the web services API
#
# NB. We need to remove the 'Expect' header due to lighttpd bug: http://redmine.lighttpd.net/issues/1017

DMS_SERVER = 'https://localhost:443'
USERNAME = 'admin'
PASSWORD = 'admin'
MIME_TYPE = 'application/pdf'

if __name__ == "__main__":
    print "DMS Uploader Started"
    if len(sys.argv) < 2:
        print "Argument required <path> or <filename>"

    try:
        path = sys.argv[1]
        if os.path.exists(path):
            if os.path.isfile(path):
                fname = os.path.basename(path)
                os.system("curl -H 'Expect: ' --user %s:%s -F 'file=@%s;type=%s' %s/api/file/%s" % (USERNAME, PASSWORD, path, MIME_TYPE, DMS_SERVER, fname))
                print " Upload OK"
            else:
                for fname in os.listdir(path):
                    filepath = os.path.join(path, fname)
                    if os.path.isfile(filepath):
                        os.system("curl -H 'Expect: ' --user %s:%s -F 'file=@%s;type=%s' %s/api/file/%s" % (USERNAME, PASSWORD, filepath, MIME_TYPE, DMS_SERVER, fname))
                        print " Upload OK"

        else:
            print "File or directory not found."
    except Exception, e:
        print "Exception %s" % (e)

