"""
Fetchmail library for Adlibre DMS

Settings Module
Role: Be able to setup mailbox and filters once in config file.

Main interest part is User settings.
Here you can define a mailbox and filter rules.

It's a standard Python module. No more, no less.
Author: Iurii Garmash (garmon1@gmail.com)
"""

from django.conf import settings
import os

#USER SETTINGS:
"""
 Email filters objects to be defined here.
 You can cast multiple filters in a list form
 for e.g. [ filter1, filter2, ... ]
 filter must be a dictionary object 
 with specified 'type', 'value' and 'delete' variables

 - 'type' can be: 'subject', 'sender', 'filename'
     - 'subject' is a filter by Email message subject specified
     - 'sender' is a filter by sender. 
         Here any string, associated with sender may be used.
         e.g.: 'user@gmail.com' or 'Iurii Garmash'
     - 'filename' is a filter to set filenames to be fetched only.
        It searches for file containing specified 'value'.
        It means you can set '.avi' and it will fetch all movie files.
        Warning! Setting 'filename' filter, without any other,
        will result processing ALL messages in chosen folder.
        it may take Lots! of time even on quick servers and connections
 - 'value' specifies the search e-mails string of your filter. 
 - 'delete' option is boolean type indicates 
       if processed messages will be deleted after attachments saved
"""
FETCH_FILTERS = {

    'filter1': { 
                'type': 'sender', # or 'subject' or 'filename'
                'value': 'Iurii',
                },
    'filter2': { 
                'type': 'filename',
                'value': 'dlanham-artifact_iphone.jpg', 
                },
    'filter3': { 
                'type': 'subject',
                'value': 'test message for pop3', 
                },
}

"""
 E-mail servers to fetch attachments from should be definrd here.
 
 - 'server_name' is your mail server address without http://
    for e.g.: 'imap.google.com'
 - 'protocol' is one of: 'IMAP4' or 'POP3'. Main handlers selector is triggered here, so choose wisely.
     Can be override in settings above.
 - 'encryption' is 'SSL' or 'none'. Says to use secure connection or not. 
     (And to use different port for encrypted protocol)
 - 'login' your username
 - 'password' your password
 - 'email_port_default' is a boolean flag indicating to use default or specific port.
 - 'email_port_number' integer value of custom email port. 
     Only used if 'email_port_default' is set to true. However must be empty string in this case.
 - 'folder_name' is your IMAP! mail folder name. 
     Folder name should be specified for IMAP processing only. 
     Otherwise not used and may be empty string or whatever.
     POP3 Protocol uses inbox only by default.
     Most common is 'INBOX', but you can use for e.g. 'Personal' or any other IMAP folder name.
     It may be your mail tag name if you use Gmail for e.g. 
     It's useful to use mailbox mail filters along with current, set here.
 - 'filters' filter names form 'FETCH_FILTERS'.
     Should be specified with list.
     for e.g. ['filter1', 'filter2', ...]
     or you can specify string 'all' 
     or whatever string set in 'USE_ALL_FILTERS_STRING' setting later here.
 - 'delete' is a boolean flag to delete messages from mailbox
 
 Warning! Try to use IMAP4 protocol if it is available.
 POP3 protocol is slower by itself and is not preferable, but available and fully functional.
"""
FETCH_EMAILS = [
    {
        'server_name': 'imap.gmail.com',
        'protocol': 'IMAP4', # or 'POP3'
        'encryption': 'SSL', # or 'none'
        'login': 'adlibre.dms.test',
        'password': 'adlibre_dms_test_password',
        'email_port_default': True,
        'email_port_number': '993', # custom mail port. not used if email_port_default = True
        'folder_name': 'INBOX', # or 'Personal' for e.g., or any other folder name
        'filters': ['filter1', 'filter2', 'filter3' ], # or 'all' for all filters applied
        'delete': True,
    },
]
# Where to save attachments to. Need to have write perm's for directory.
STORE_FILES_PATH = os.path.join(settings.PROJECT_PATH, '../../emails_temp/') #emails_temp in root project dir
# Will be appended to the end of filename if same exists in output directory.
FILENAME_EXISTS_CHANGE_SYMBOL = '_' 

# OVERRIDE DEFAULT SETTINGS:
# Useful for building models for e.g.
# to specify your own internal strings and numbers.
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
USE_ALL_FILTERS_STRING = 'all'
