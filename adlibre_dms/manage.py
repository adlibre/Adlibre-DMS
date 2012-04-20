#!/usr/bin/env python

# Customised manage.py

from django.core.management import execute_manager
try:
    from adlibre_dms import settings # this will also import the local_settings.py in this directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'adlibre_dms.settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
