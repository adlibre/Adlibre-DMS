#!/usr/bin/env python
import sys
import os
#from subprocess import Popen, PIPE

# TODO: as per https://redmine.adlibre.net/issues/28 need some more features:
# Logging
# optional append (pdf / tiff),
# optional fail if file exists.

FASTTRACK_SERVER = 'http://localhost:8000'

if __name__ == "__main__":
    print "Fasttrack uploader"
    if len(sys.argv) < 2:
        print "use --help to display available parameters"

    try:
        path = sys.argv[1]
        if os.path.exists(path):
            if os.path.isfile(path):
                os.system("curl -F 'filename=@%s' %s/api/file/" % (path, FASTTRACK_SERVER))
                print "Upload OK"
            else:
                for fname in os.listdir(path):
                    filename = "%s/%s" % (path, fname)
                    if os.path.isfile(filename):
                        os.system("curl -F 'filename=@%s' %s/api/file/" % (filename, FASTTRACK_SERVER))
                        print "Upload OK"

        else:
            print "File or directory not found."
    except:
        pass

