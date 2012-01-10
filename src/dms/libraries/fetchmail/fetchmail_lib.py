"""
Module: Fetchmail library for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)

Details:

Main Library Module

Made for downloading attachments from email account
based on certain filtration levels.
For e.g. extracting attachments from emails 
of certain sender ('user@gmail.com' or even 'Iurii Garmash'),
or with subject ('accounting report' or 'file:')...

Please see models.py documentation of this library for usage examples
Please see app_settings.py documentation for useful settings to be set

"""

from libraries.fetchmail.app_settings import PROTOCOL_TYPE_IMAP4, PROTOCOL_TYPE_POP3
from libraries.fetchmail.settings_reader import read_settings
from libraries.fetchmail.handler_imap import connect_imap4, imap_email_processor, imap_discover_folders, process_letters_imap
from libraries.fetchmail.handler_pop3 import connect_pop3, select_letters_pop3, download_letters_pop3, process_letters_pop3, delete_pop3_messages

def process_email(email_obj=None, quiet=False):
    """
    Main email processing module
    Processes specified email.
    """
    if not email_obj:
        email_objects = read_settings(quiet=quiet)
    else:
        email_objects = [email_obj]
    for email_object in email_objects:
        connection = login_server(email_object, quiet=quiet)
        if connection.connection_type_info == PROTOCOL_TYPE_IMAP4:
            mail_folder = imap_discover_folders(connection, folder_name=email_object.folder_name, quiet=quiet)
            emails, filename_filter = imap_email_processor(folder=mail_folder, filters=email_object.filters, quiet=quiet)
            if emails:
                filenames = process_letters_imap(emails=emails, email_obj=email_object, filename_filter=filename_filter, mail_folder=mail_folder, quiet=quiet)
                connection.logout()
                if not filenames and not quiet: return 'No attachments received'
                if filenames:
                    return filenames
                else:
                    if not quiet:
                        print 'No messages with specified parameters exist'
                    return 'Done'
            else:
                connection.logout()
                if not quiet:
                    print 'No messages with specified parameters exist'
                return 'Done'
        elif connection.connection_type_info == PROTOCOL_TYPE_POP3:
            fetch_letters, filename_filter_applied = select_letters_pop3(connection, email_object.filters, quiet=quiet)
            if fetch_letters == []: 
                if not quiet:
                    print 'No messages with specified parameters exist'
                return 'Done' 
            messages = download_letters_pop3(fetch_letters, connection, quiet=quiet)
            result = process_letters_pop3(messages, filename_filter_applied, quiet=quiet)
            if email_object.delete_messages_flag:
                delete_pop3_messages(fetch_letters, connection, quiet=quiet)
            if not quiet:
                return result

def login_server(email_obj, quiet):
    """
    Logs in current email_object
    Returns logged in server object
    """
    if email_obj.protocol == PROTOCOL_TYPE_POP3:
        server = connect_pop3(email_obj)
    elif email_obj.protocol == PROTOCOL_TYPE_IMAP4:
        server = connect_imap4(email_obj)
    if not quiet:
        print('\nLogin successful with '+str(server.connection_type_info))
    return server
