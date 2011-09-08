#!/usr/bin/env python

import sys
import os

#
# Adlibre DMS: Example of command line uploading using the web services API
#


DMS_SERVER = 'http://localhost:8000'

if __name__ == "__main__":
    print "DMS Uploader"
    if len(sys.argv) < 2:
        print "use --help to display available parameters"

    try:
        path = sys.argv[1]
        if os.path.exists(path):
            if os.path.isfile(path):
                os.system("curl -F 'file=@%s' %s/api/file/" % (path, DMS_SERVER))
                print "Upload OK"
            else:
                for fname in os.listdir(path):
                    filename = "%s/%s" % (path, fname)
                    if os.path.isfile(filename):
                        os.system("curl -F 'filename=@%s' %s/api/file/" % (filename, DMS_SERVER))
                        print "Upload OK"

        else:
            print "File or directory not found."
    except:
        pass

