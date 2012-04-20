# Settings file for when we install using pip in non development scenario

from adlibre_dms.settings import *

# HACK: Here be magic and import voodoo...
# This file exists just to make manage.py happy when passing --settings= parameter.
# Put all your config in local_settings.py

## Overrides for our project layout in a standard deployment

# Database Location project_root/db/
import os
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.abspath(os.path.join(PROJECT_PATH, '..', 'db', 'dms.sqlite')),
        }
}

MEDIA_ROOT = os.path.abspath(os.path.join(PROJECT_PATH, '..', 'www', 'media'))
STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_PATH, '..', 'www', 'static'))

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, '..', 'custom_static'),
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, '..', 'custom_templates'),
    os.path.join(PROJECT_PATH, 'templates'),
)

###
