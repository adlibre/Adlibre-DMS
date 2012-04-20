"""
Module: Fetchmail library for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)

Details: Main Settings Processor

Role: Converts settings from easy readable to "library suitable" format.

"""
from adlibre.fetchmail.models import Email_object, Filter_object
from adlibre.fetchmail.app_settings import USE_ALL_FILTERS_STRING, FETCH_EMAILS, FETCH_FILTERS

def read_settings(quiet=False):
    """
    Helper to read Library's settings and instantate them to desirable format.
    takes data from imported upper Python settings module,
    parses and instantanes them to format used in library.
    
    Returns Email_object()
    """
    emails = []
    for email in FETCH_EMAILS:
        mailbox = Email_object()
        mailbox.server_name = email['server_name']
        mailbox.protocol = email['protocol']
        mailbox.encryption = email['encryption']
        mailbox.login = email['login']
        mailbox.password = email['password']
        mailbox.email_port_default = email['email_port_default']
        mailbox.email_port_number = email['email_port_number']
        mailbox.folder_name = email['folder_name']
        mailbox.filters = read_filters(email['filters'])
        mailbox.delete_messages_flag = email['delete']
        emails.append(mailbox)
        if not quiet:
            print '\nWill process server:'+str(mailbox)
    if emails == []:
        return 'No mailbox specified or error in settings.\n'
    return emails

def read_filters(filter_names=False):
    """
    Helper function to process filters. 
    Returns list of ALL filters in settings by default.
    
    - In case of specified filter_names, returns list of filter objects with those names.
        'filter_names' must be in settings filters format like:
        "['filter1,', 'filter2', ... ]"
    - Else returns list of all filter objects, specified in settings.
    """
    filters = []
    if filter_names:
        for filter_name in filter_names:
            for key, email_filter in FETCH_FILTERS.iteritems():
                filter_instance = Filter_object()
                filter_instance.name = email_filter
                filter_instance.type = email_filter['type']
                filter_instance.value = email_filter['value']
                if filter_name == key:
                    filters.append(filter_instance)
                
    elif filter_names == USE_ALL_FILTERS_STRING:
        for key, email_filter in FETCH_FILTERS.iteritems():
            filter_instance = Filter_object()
            filter_instance.name = key
            filter_instance.type = email_filter['type']
            filter_instance.value = email_filter['value']
            filters.append(filter_instance)
    return filters
