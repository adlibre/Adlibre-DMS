"""
Settings file for when we install using pip in non development scenario
Contains overrides for our project layout in a standard deployment.
"""

from adlibre_dms.settings import * # Import global settings

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
DOCUMENT_ROOT = os.path.join(PROJECT_PATH, '..', 'documents')
COMPRESS_ROOT = STATIC_ROOT

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, '..', 'custom_static'),
)

TEMPLATE_DIRS = (os.path.join(PROJECT_PATH, '..', 'custom_templates'),) + TEMPLATE_DIRS

import logging
#from adlibre_dms.settings import NoMessageFailuresFilter # already imported
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(name)s %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s %(message)s'
        },
        },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
            },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(PROJECT_PATH, '..', 'log', 'dms.log'),
            'when': 'midnight',
            'interval': 1, # 1 day
            'backupCount': 14, # two weeks
            'formatter': 'verbose',
            },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            }
    },
    'filters': {
        'no_message_failures': {
            '()': NoMessageFailuresFilter,
            },
        },
    'loggers': {
        # Filter out restkit to null
        'restkit': {
            'handlers': ['null',],
            'level': 'DEBUG',
            'propagate': False,
            },
        # Default logger
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'filters': ['no_message_failures'],
            'propagate': True,
            },
        # DMS logger
        'dms': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
            },
        # Django 500 error logger
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
            'filters': ['no_message_failures'],
            },
        }
}

# Email settings
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'testing@example.com' # Override in your local_settings

# This will import the local_settings in our virtual_env subdir next to manage.py.
try:
    from local_settings import *
except ImportError:
    pass

###
