"""
Module: Fetchmail library for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)

Details:

Handler for POP3 protocol.

Role: Authenticates, Applies filters, Downloads messages, Deletes from server

"""

from libraries.fetchmail.app_settings import ENCRYPTION_EXISTS, DEFAULT_POP3_SSL_PORT, ENCRYPTION_ABSENT, DEFAULT_POP3_PORT
from libraries.fetchmail.app_settings import DEFAULT_FILTER_SENDER_NAME, DEFAULT_FILTER_SUBJECT_NAME, DEFAULT_FILTER_FILENAME_NAME
from libraries.fetchmail.processor import process_single_letter
import poplib
import rfc822, string, StringIO

def connect_pop3(email_obj):
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
    pop3_server.user(email_obj.login)
    pop3_server.pass_(email_obj.password)
    pop3_server.connection_type_info = email_obj.protocol
    return pop3_server

def select_letters_pop3(server, filters, quiet=False):
    """
    Processes message queue according to specified filters.
    Download's available message headers according to POP3 protocol.
    Checks every header to meet all filter's criteria.
    Tries to implement behavior similar to Python imaplib's mailbox.search() method.
    
    Takes authenticated pop3 server instance and email filters.
    Returns a tuple: list of message id's 
    and a filename_filter_applied = False or file filter value if it is applied.
    """
    #retrieving headers of all server messages
    msg_ids_list = []
    resp, items, octets = server.list()
    messagesInfo = server.list()[1]
    print messagesInfo
    for item in items:
        msg_id, size = item.split()
        response, lines, octets = server.top(msg_id, 3)
        #converting to rfc822 compatible format
        text = string.join(lines, "\n")
        file = StringIO.StringIO(text)
        message = rfc822.Message(file)
        message_pass, filename_filter_applied = filter_message_pop3(message, filters, quiet=quiet)
        if message_pass:
            msg_ids_list.append(msg_id)
    if not quiet:
        print "Will process message id's: "
        print msg_ids_list
        if filename_filter_applied:
            print 'Filename search string value: '+str(filename_filter_applied)
    return msg_ids_list, filename_filter_applied

def filter_message_pop3(message, filters, quiet=False):
    """
    Sorts messages by headers, according to filters applied.
    'message_header' must be an RFC822 formatted message.
    'filters' usually is Email_object().filters value (Filters list)
    
    Returns tuple of True/False if message has passed filter check
    and a filefilter_used = False or file filter value if it is applied.
    """
    has_sender_filter = False
    has_subject_filter = False
    message_pass = False
    # checking if message has filename filter
    filename_filter_applied = False
    for filter_ in filters:
        if filter_.type == DEFAULT_FILTER_SENDER_NAME:
            has_sender_filter = True
        if filter_.type == DEFAULT_FILTER_SUBJECT_NAME:
            has_subject_filter = True
        if filter_.type == DEFAULT_FILTER_FILENAME_NAME:
            filename_filter_applied = filter_.value
    # applying 'sender' filter first and checking subject after this
    # made this feature like so, to copy imaplib mailbox.search() behavior
    checked_sender = check_sender(message, filters)
    if not has_subject_filter:
        message_pass = checked_sender
    else:
        message_pass = check_subject(message, filters)
    return message_pass, filename_filter_applied

def check_sender(message, filters):
    """
    Helper to check message for 'sender' filter value
    """
    message_pass = False
    for filter_ in filters:
        if filter_.type == DEFAULT_FILTER_SENDER_NAME:
            for key, value in message.items():
                if key == 'from':
                    if value.rfind(filter_.value) != -1:
                        message_pass = True
    return message_pass

def check_subject(message, filters):
    """
    Helper to check message for 'subject' filter value
    """
    message_pass = False
    for filter_ in filters:
        if filter_.type == DEFAULT_FILTER_SUBJECT_NAME:
            for key, value in message.items():
                if key == 'subject':
                    if value.rfind(filter_.value) != -1:
                        message_pass = True
    return message_pass

def download_letters_pop3(letters_list, server, quiet=False):
    """
    Downloads a list of messages from server with POP3
    """
    messages = []
    for item in letters_list:
        response, lines, octets = server.retr(item)
        #converting to desirable format for processor
        text = string.join(lines, "\n")
        messages.append(text)
    if not quiet:
        print 'Done downloading, Processing...'
    return messages

def process_letters_pop3(messages, filename_filter_applied, quiet=False):
    """
    Proxy to process all letters in queue one by one.
    """
    for message in messages:
        try:
            process_single_letter(message, filename_filter_applied, quiet=quiet)
            if not quiet:
                print 'Done converting/saving attachments...'
        except:
            if not quiet:
                print 'Error processing message!'
            return 'Error'
    return 'Done'

def delete_pop3_messages(messages, server, quiet=False):
    """
    Helper to delete downloaded messages from server using POP3 protocol.
    """
    print 'About to delete messages fetched.'
    for message in messages:
        print message
        server.dele(message)
    if not quiet:
        print "Deleted message id's:"+ str(messages)
    