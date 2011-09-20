"""
Fetchmail library for Adlibre DMS

Settings Module
Author: Iurii Garmash (garmon1@gmail.com)

Main interest part is User settings.
Here you can define a mailbox and filter rules.

It's a standard Python module. No more, no less.
"""

from django.conf import settings
import os

#USER SETTINGS:
# Email filters objects to be defined here.
# You can cast multiple filters in a list form
# for e.g. [ filter1, filter2, ... ]
# filter must be a dictionary object 
# with specified 'type', 'value' and 'delete' variables
#
# - 'type' can be: 'subject', 'sender', 'filename'
# - 'value' specifies the search e-mails string of your filter. 
#       For e.g.: 'user@gmail.com' or 'accounting report'
# - 'delete' option is boolean type indicates 
#       if processed messages will be deleted after attachments saved
FETCH_FILTERS = {

    'filter1': { 
                'type': 'sender',
                'value': 'Iurii',
                },
    'filter2': { 
                'type': 'subject',
                'value': 'test message 3', 
                },
}

# E-mail servers to fetch attachments from. 
# Structure same as filters object.
# Filters should be specified with list.
#     for e.g. ['filter1', 'filter2', ...] 
# Folder name should be specified (For IMAP processing only)
# TODO: document this after resolving issue with folders and implementing POP3
#     Most common is 'INBOX', but you can use for e.g. 'Personal' or any other IMAP folder name.
# delete is a flag to delete messages from mailbox
FETCH_EMAILS = [
    {
        'server_name': 'imap.gmail.com',
        'protocol': 'IMAP4', # TODO: or 'POP3'
        'encryption': 'SSL', # or 'none'
        'login': 'adlibre.dms.test',
        'password': 'adlibre_dms_test_password',
        'email_port_default': False,
        'email_port_number': '993', # custom mail port. not used if email_port_default = True
        'folder_name': 'INBOX', # or 'Personal' for e.g., or any other folder name
        'filters': ['filter1', 'filter2', ], # or 'all' for all filters applied
        'delete': False,
    },
]
# Where to save attachments to. Need to have write perm's for directory.
STORE_FILES_PATH = os.path.join(settings.PROJECT_PATH, '../../emails_temp/') #emails_temp in root project dir
FILENAME_EXISTS_CHANGE_SYMBOL = '_'

# OVERRIDE DEFAULT SETTINGS:
# Do not touch if not certain!
# auth defaults
PROTOCOL_TYPE_IMAP4 = 'IMAP4'
PROTOCOL_TYPE_POP3 = 'POP3'
ENCRYPTION_EXISTS = 'SSL'
ENCRYPTION_ABSENT = 'none'
DEFAULT_POP3_PORT = 110
DEFAULT_POP3_SSL_PORT = 995
DEFAULT_IMAP4_PORT = 143
DEFAULT_IMAP4_SSL_PORT = 993

# mailbox defaults
DEFAULT_EMAIL_FOLDER_NAME = 'INBOX'

#processing types
DEFAULT_FILTER_SENDER_NAME = 'sender'
DEFAULT_FILTER_SUBJECT_NAME = 'subject'
DEFAULT_FILTER_FILENAME_NAME = 'filename'

