#!/usr/bin/env python
import sys
import os
from subprocess import Popen, PIPE

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
                pass
        else:
            print "File or directory not found."
    except:
        pass

