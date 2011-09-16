# Mail management script for Adlibre DMS
#
# - Authenticates with IMAP4/POP3 protocols
# - Searches mailbox for messages based on provided filters
# - Saves attachments to temporary folder

from django.core.management.base import BaseCommand
from django.conf import settings
import imaplib
import poplib
import email
import mimetypes
import os


from optparse import make_option
#from compiler.ast import Function

# settings:
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
# file operations
DEFAULT_TEMP_FILES_PATH = os.path.join(settings.PROJECT_PATH, '../../emails_temp/') #documents/emails_temp in root project dir


# TODO: email object to override in future
# need 2 discuss about how e-mails will be stored in an app
# maybe we will use a Django model here
# Emulating Model entry for now.

#FIlter model
class Filter_object(object):
    def __init__(self):
        self.type = 'sender' # TODO: subject, sender, filename
        self.value = 'Iurii'
        self.delete = False  # TODO: delete messages on server after processing ability 

# another instanced filter model
filter_object2 = Filter_object()
filter_object2.type = 'subject'
filter_object2.value = 'test message 3'

# email_obj model
class Email_object(object):
    def __init__(self):
        self.server_name ='imap.gmail.com'
        self.protocol = 'IMAP4' # TODO: or 'POP3'
        self.encryption = 'SSL' # or 'none'
        self.login = 'adlibre.dms.test'
        self.password = 'adlibre_dms_test_password'
        self.email_port_default = False
        self.email_port_number = '993' #custom mail port. not used if email_port_default = True
        self.folder_name = 'INBOX'
        self.filter = [ Filter_object(), filter_object2 ]


class Command(BaseCommand):
    
    def __init__(self):
        BaseCommand.__init__(self)
        self.option_list += (
            make_option(
                '--quiet', '-q',
                default=False,
                action='store_true',
                help='Hide all command output'),
            )
    help = "Fetches mail from IMAP/POP3 server and feeds it's attachments to Adlibre API"
    
    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        if not quiet:
            self.stdout.write('Starting to process e-mails')
        response = process_email(quiet=quiet)
        if not quiet:
            self.stdout.write(str(response))
        

def process_email(quiet=False):
    """
    Main email processing scheme
    """
    email_object = Email_object()
    connection = login_server(email_object, quiet=quiet)
    if connection.connection_type_info == PROTOCOL_TYPE_IMAP4:
        mail_folder = discover_folders(connection, folder_name=email_object.folder_name, quiet=quiet)
        emails = imap_email_processor(folder=mail_folder, filters=email_object.filter, quiet=quiet)
        
        if emails:
            # TODO: filenames processing through API
            filenames = process_letters(emails=emails, mail_folder=mail_folder, quiet=quiet)
            connection.logout()
            if not filenames and not quiet: return 'No attachments received'
            if filenames:
                result = feed_API(filenames, quiet=quiet)
                return result
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
        #print 'Message %s\n%s\n' % (letter_number, data[0][1])
        result += process_single_letter(data)
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
        # FIXME: Applications should really sanitize the given filename so that an
        # email message can't be used to overwrite same files
        # e.g. we got 2 different messages with identical filenames
        if filename:
            if not quiet:
                print ("Fetched filename:"+ str(filename));
            fp = open(os.path.join(DEFAULT_TEMP_FILES_PATH, filename), 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()
            filenames += [filename]
    return filenames
    
    
def feed_API(filenames, quiet=False):
    """
    Feeds attachments to the API.
    Takes filenames array. 
    Feeds API with those files.
    Files should already be in folder.
    """
    for filename in filenames:
        if not quiet: print 'Feeding API with file: '+str(filename)
    # TODO: develop this function to not only store files to temp folder, but to actually feed the API
    return filenames
