import os, sys

# Add the path to 3rd party django application and to django itself.
sys.path.append('/srv/www/dms/src')

os.environ['DJANGO_SETTINGS_MODULE'] = 'dms.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
