"""
Fetchmail library for Adlibre DMS

Made for downloading attachments from email account
based on certain filtration levels.
For e.g. extracting attachments from emails 
of certain sender ('user@gmail.com' or even 'Iurii Garmash'),
or with subject ('accounting report' or 'file:')...

Please see models.py documentation of this library for usage examples

Author: Iurii Garmash (garmon1@gmail.com)
"""

import imaplib
import poplib
import email

from libraries.fetchmail.app_settings import *
from libraries.fetchmail.models import *
from libraries.fetchmail.settings_reader import *

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
            mail_folder = discover_folders(connection, folder_name=email_object.folder_name, quiet=quiet)
            emails = imap_email_processor(folder=mail_folder, filters=email_object.filters, quiet=quiet)
            if emails:
                filenames = process_letters(emails=emails, mail_folder=mail_folder, quiet=quiet)
                connection.logout()
                if not filenames and not quiet: return 'No attachments received'
                if filenames:
                    result = feed_API(filenames, quiet=quiet)
                    return result
                else:
                    if not quiet:
                        print 'No messages with specified parameters exist'
                    return 'Done'
            else:
                connection.logout()
                if not quiet:
                    print 'No messages with specified parameters exist'
                return 'Done'


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

def connect_pop3(email_obj):
    # FIXME: implement this part
    # main target is imap4 so this part is not finished (tested) for now
    """ 
    Connects a server with POP3 PROTOCOL
    Returns authenticated server instance
    """
    if email_obj.encryption == ENCRYPTION_EXISTS:
        if email_obj.email_port_default: 
            pop3_server = poplib.POP3_SSL(email_obj.server_name, DEFAULT_POP3_SSL_PORT)
        else:
            pop3_server = poplib.POP3_SSL(email_obj.server_name, email_obj.email_port_number)
    elif email_obj.encryption == ENCRYPTION_ABSENT:
        if email_obj.email_port_default:
            pop3_server = poplib.POP3(email_obj.server_name, DEFAULT_POP3_PORT)
        else:
            pop3_server = poplib.POP3(email_obj.server_name, email_obj.email_port_number)
    pop3_server.user_(email_obj.login)
    pop3_server.pass_(email_obj.password)
    pop3_server.connection_type_info = email_obj.protocol
    return pop3_server

def connect_imap4(email_obj):
    """ 
    Connects a server with IMAP4 PROTOCOL
    Returns authenticated server instance
    appends server_insrtance.connection_type_info with connection type data
    
    """
    if email_obj.encryption == ENCRYPTION_EXISTS:
            if email_obj.email_port_default: 
                imap_server = imaplib.IMAP4_SSL(email_obj.server_name, DEFAULT_IMAP4_SSL_PORT)
            else:
                imap_server = imaplib.IMAP4_SSL(email_obj.server_name, email_obj.email_port_number)
            
    elif email_obj.encryption == ENCRYPTION_ABSENT:
            if email_obj.email_port_default: 
                imap_server = imaplib.IMAP4(email_obj.server_name, DEFAULT_IMAP4_PORT)
            else:
                imap_server = imaplib.IMAP4(email_obj.server_name, email_obj.email_port_number)
    imap_server.login(email_obj.login, email_obj.password)
    imap_server.connection_type_info = email_obj.protocol
    return imap_server

# TODO: add some algorithm of selecting folders in mailbox
def discover_folders(connection, folder_name=DEFAULT_EMAIL_FOLDER_NAME, quiet=False):
    """ 
    Suits for finding folders in connection, as there may be many occasions.
    # TODO: create connection with POP3
    """
    connection.select(folder_name)
    if not quiet:
        print 'Processing folder '+str(folder_name)
    return connection

def imap_email_processor(folder, filters, quiet=False):
    """
    Takes folder instance (mailbox folder)
    and finds messages, according to filters, inside it.
    """
    # constructing filter string to select messages
    filter_string = '('
    for filter in filters:
        if filter.type == DEFAULT_FILTER_SENDER_NAME:
            if filter_string != '(': filter_string += ' '
            filter_string += 'FROM "'+str(filter.value)+'"'
        if filter.type == DEFAULT_FILTER_SUBJECT_NAME:
            if filter_string != '(': filter_string += ' '
            filter_string += 'SUBJECT "'+str(filter.value)+'"'
    filter_string += ')'
    if not quiet:
        print 'Message filter:'
        print filter_string
    status, msg_ids_list = folder.search(None, filter_string)
    if not quiet:
        print 'Status: '+str(status)
        print "Message id's to be fetched:"
        print msg_ids_list
    if msg_ids_list == ['']:
        return None
    else:
        return msg_ids_list

def process_letters(emails, mail_folder, quiet=False):
    """
    Processes a list of fetched messages ID's
    for e.g.: ['1 2 3']
    """
    letters = emails[0].split()
    result = []
    for letter_number in letters:
        if not quiet:
            print "About to fetch email ID's: "+str(letter_number)
        status, data = mail_folder.fetch(letter_number, '(RFC822)')
        # uncomment to print formated message
        #print 'Message %s\n%s\n' % (letter_number, data[0][1])
        result += process_single_letter(data, quiet=quiet)
    return result
        
def process_single_letter(msg, quiet=False):
    """
    Processing single message.
    Takes message instance ('msg' must be an RFC822 formatted message.)
    Scans for attachments and saves them to temporary folder.
    Returns file list.
    """
    # 
    message = email.message_from_string(str(msg[0][1]))
    filenames = []
    for part in message.walk():
        #print (part.as_string() + "\n")
        # multipart/* are just containers
        if part.get_content_maintype() == 'multipart':
            continue
        filename = part.get_filename()
        if filename:
            if not quiet:
                print ("Fetched filename:"+ str(filename));
            # cycle file existence check/renaming sequence
            file_exists = os.path.isfile(os.path.join(STORE_FILES_PATH, filename))
            if file_exists:
                if not quiet:
                    print 'File already exists: '+str(filename)
                new_file_exists = True
                new_filename = filename
                while new_file_exists:
                    directory, filename = os.path.split(new_filename)
                    filename_string, extension = os.path.splitext(new_filename)
                    new_filename_string = filename_string + FILENAME_EXISTS_CHANGE_SYMBOL
                    new_filename = new_filename_string + extension
                    new_file_exists = os.path.isfile(os.path.join(STORE_FILES_PATH, new_filename))
                filename = new_filename
                if not quiet:
                    print 'Renamed to: ' + str(filename)
            fp = open(os.path.join(STORE_FILES_PATH, filename), 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()
            filenames += [filename]
    return filenames
    
# Prohibited due to priority changes
def feed_API(filenames, quiet=False):
    """
    Feeds attachments to the API.
    Takes filenames array. 
    Feeds API with those files.
    Files should already be in folder.
    """
    #for filename in filenames:
    #    if not quiet: print 'Feeding API with file: '+str(filename)
    # TODO: develop this function to not only store files to temp folder, but to actually feed the API
    return filenames
