from dms.settings import *

DEMO = False
DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
	('Andrew Cutler', 'andrew@adlibre.com.au'),
)

MANAGERS = ADMINS

# remove fcgi script name from url (lighttpd)
FORCE_SCRIPT_NAME = ''