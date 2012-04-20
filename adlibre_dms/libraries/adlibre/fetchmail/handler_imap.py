"""
Module: Fetchmail library for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)

Details:

Handler for IMAP4 protocol.

Role: Authenticates, Applies filters, Downloads messages, Deletes from server

"""
from adlibre.fetchmail.app_settings import ENCRYPTION_EXISTS, DEFAULT_IMAP4_SSL_PORT, ENCRYPTION_ABSENT
from adlibre.fetchmail.app_settings import DEFAULT_IMAP4_PORT, DEFAULT_FILTER_SENDER_NAME, DEFAULT_FILTER_SUBJECT_NAME
from adlibre.fetchmail.app_settings import DEFAULT_FILTER_FILENAME_NAME, DEFAULT_EMAIL_FOLDER_NAME
from adlibre.fetchmail.processor import process_single_letter
import imaplib

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

def imap_email_processor(folder, filters, quiet=False):
    """
    Takes folder instance (mailbox folder) and filters from email_object.
    Finds messages, according to filters, inside it.
    
    Returns tuple of messages found and a filename filter flag
    """
    filename_filter = False
    # constructing filter string to select messages
    filter_string = '('
    for filter_ in filters: 
        if filter_.type == DEFAULT_FILTER_SENDER_NAME:
            if filter_string != '(': filter_string += ' '
            filter_string += 'FROM "'+str(filter_.value)+'"'
        if filter_.type == DEFAULT_FILTER_SUBJECT_NAME:
            if filter_string != '(': filter_string += ' '
            filter_string += 'SUBJECT "'+str(filter_.value)+'"'
        if filter_.type == DEFAULT_FILTER_FILENAME_NAME:
            filename_filter = filter_.value
    filter_string += ')'
    if not quiet:
        print 'Message filter:'
        print filter_string
        if filename_filter:
            print 'FIltered filename: '+str(filename_filter)
    status, msg_ids_list = folder.search(None, filter_string)
    if not quiet:
        print "Message id's to be fetched:"
        print msg_ids_list
    if msg_ids_list == ['']:
        return None, filename_filter
    else:
        return msg_ids_list, filename_filter

def imap_discover_folders(connection, folder_name=DEFAULT_EMAIL_FOLDER_NAME, quiet=False):
    """ 
    Suits for finding folders in connection, as there may be many occasions.
    # TODO: create connection with POP3
    """
    connection.select(folder_name)
    if not quiet:
        print 'Processing folder '+str(folder_name)
    return connection

def process_letters_imap(emails, email_obj, filename_filter, mail_folder, quiet=False):
    """
    Processes a list of fetched messages ID's
    for e.g.: ['1 2 3']
    Returns list of lists of attachment's filenames for every email processed
    for e.g.: [ ['filename1.txt', 'filename2.txt'], ['filenae3.txt', 'filename4.txt', filename5.txt' ... ], ... ]
    """
    letters = emails[0].split()
    result = []
    for letter_number in letters:
        if not quiet:
            print "About to fetch email ID's: "+str(letter_number)
        status, data = mail_folder.fetch(letter_number, '(RFC822)')
        # uncomment to print formated message
        #print 'Message %s\n%s\n' % (letter_number, data[0][1])
        result += process_single_letter(msg=data, filter_filename=filename_filter, quiet=quiet)
        if email_obj.delete_messages_flag:
            delete_letter_imap(letter_number=letter_number, mail_folder=mail_folder, quiet=quiet)
    return result

def delete_letter_imap(letter_number, mail_folder, quiet=False):
    """
    Helper function to delete a message from IMAP4 mailbox
    takes int(letter_number)
    mail_folder = IMAP4 mail folder object, connected and containing desired message id
    """
    try:
        typ, response = mail_folder.fetch(letter_number, '(FLAGS)')
        typ, response = mail_folder.store(letter_number, '+FLAGS', r'(\Deleted)')
        # may be used in some cases, but connection.close(), we're using overrides this method
        #typ, response = mail_folder.expunge()
        if not quiet:
            print 'Deleted message id:', str(letter_number)
    except:
        if not quiet:
            print 'Error deleting message %s from mailbox' , str(letter_number)
