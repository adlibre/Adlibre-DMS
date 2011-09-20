"""
Fetchmail library for Adlibre DMS

Main objects module.
Defines Fetcher_object() class for programmatic library manipulations 
and 2 main object types used in the library: Filter_object() and Email_object()

Fetcher can be instantated to be used in views or models.
usage:

from libraries.fetchmail.models import *

#creating filters objects first
email_filter1 = Filter_object()
email_filter2 = Filter_object()
email_filter1 = email_filter1.create_filter(filter_type='sender', value='Iurii')
email_filter2 = email_filter2.create_filter(filter_type='subject', value='test message 3')

# creating email object with this filters
email = Email_object()
email = email.create_email(server_name='imap.gmail.com',
                           login='test_login',
                           password='test_password',
                           filters = [email_filter1, email_filter2])

# processing mail with Fetcher() instance
fetcher = Fetcher_object()
fetcher.fetchmail(email=email)

Filter is an object to contain filters used for choosing email messages to fetch.
Email is widely used in processor to store default mailbox values for processing.

Author: Iurii Garmash (garmon1@gmail.com)
"""

from libraries.fetchmail.fetchmail_lib import *
from libraries.fetchmail.app_settings import *

class Fetcher_object(object):
    """
    Defines main fetchmail module to be used in library 
    for programmatic calls.
    
    for e.g.:
    fetcher = Fetcher_object()
    fetcher.email = Email_object()  (Read Email_object() help for more info)
    fetcher.process_email()
    """
    
    def __init__(self):
        self.email = ''
    
    def fetchmail(self, email=False, quiet=True):
        """
        Main processing function.
        Checks for right usage and processes email
        """
        if not email:
            raise FetchmailExeption('Can not proceed. No mail object given.')
        try:
            process_email(email_obj=email, quiet=quiet)
        except:
            raise FetchmailExeption('Cannot process emails because of error.')

class Filter_object(object):
    """
    Creating empty Filter object
    not the most right way to do so.
    Must use:
    email_filter = Filter_object().create_filter(filter_type='sender')
    """
    def __init__(self):
        self.name = ''
        self.type = '' # TODO: subject, sender, filename
        self.value = ''
    
    def create_filter(self, filter_type='', name='',  value='', delete=False):
        """
        Creates a filter instance with specified parameters.
        
        - 'filter_type' must be str(): 'subject', 'sender', 'filename', or some changed from defaults string from app_settings
        - 'value' is a u'' filter value. For e.g. 'Iurii Garmash' or 'example@gmail.com'
        - 'name' is not necessary to be specified except possible future uses e.g. 'Messages from my mother'
        """
        # checking for filter type
        if (filter_type == DEFAULT_FILTER_SUBJECT_NAME) or (filter_type == DEFAULT_FILTER_SENDER_NAME) or (filter_type == DEFAULT_FILTER_FILENAME_NAME):
            pass
        else:
            raise FetchmailExeption('Wrong filter type specified!')
        self.name = str(name)
        self.type = str(filter_type)
        self.value = unicode(value)
        return self
    
    def __str__(self):
        return str(self.type+'@'+str(self.value))
    
    def __unicode__(self):
        return unicode(self.type+u'@'+str(self.value))

class Email_object(object):
    """
    Creating empty Email object
    not so right way to instantate a Email_obj()
    
    use method 'create_email(params)' instead...
    for e.g.
    
    email = Email_object.create_email(server_name='imap.google.com',
                                      login='testing',
                                      password='testing')
    
    """
    def __init__(self):
        self.server_name =''
        self.protocol = ''  # TODO: Add a POP3 server connection protocol
        self.encryption = ''
        self.login = ''
        self.password = ''
        self.email_port_default = True
        self.email_port_number = ''
        self.folder_name = DEFAULT_EMAIL_FOLDER_NAME
        self.filters = 'all'
        self.delete_messages_flag = False
    
    def __str__(self):
        return str(self.login)+'@'+str(self.server_name)
    
    def __unicode__(self):
        return unicode(self.login)+u'@'+unicode(self.server_name)
    
    def create_email(self, 
               server_name,
               login, 
               password, 
               protocol='IMAP4', 
               encryption='SSL', 
               port=False,
               folder_name=DEFAULT_EMAIL_FOLDER_NAME,
               filters=False,
               delete=False):
        """
        Creates a email object instance with specified parameters.
        
        all data, except boolean values, login and password are str() 
        login and password are u''
        type suggestions specified are valid if 'app_settings' is not overriding them
        
        - 'server_name' is mandatory. For e.g. 'imap.google.com'
        - 'protocol' must be 'IMAP4' or 'POP3'. Default is IMAP4
        - 'encryption' must be 'SSL' or 'none'. Default is SSL
        - 'login' your mail server login
        - 'password' your mail server password. Must not be encrypted! (in u'' or any convertable format. for e.g. u'password')
        - 'port' may be specified to override default connection port for mail. Default is False.
        - 'folder_name' is your mailbox name for letters to process.
            It's useful like in Gmail you have filters that sort new mail with Tags. You can set a Tag name here.
            You can this way override INBOX search and use mailbox filters for mail
            to be sorted to another folder with for e.g. Gmail filters and processed by fetchmail afterwards.
        - 'filters' is a Python list! of filter objects.
            For e.g.:
            [Filter_obj(), Filter_obj(), ...]
            Warning! If no filters specified fetchmail will process all mail in specified folder
            and by default it is 'INBOX'.
        - 'delete' flag either to delete messages from this mailbox upon processing or not. Default is False.
        """
        # clean.protocol
        if (protocol == PROTOCOL_TYPE_IMAP4) or (protocol == PROTOCOL_TYPE_POP3):
            pass
        else:
            raise FetchmailExeption('Error in "protocol" provided')
        if (encryption == ENCRYPTION_EXISTS) or (encryption == ENCRYPTION_ABSENT):
            pass
        else:
            raise FetchmailExeption('Error in "encryption" provided')
        self.server_name=str(server_name)
        self.protocol=str(protocol)
        self.encryption=str(encryption)
        self.login = unicode(login)
        self.password = unicode(password)
        if port:
            try:
                self.email_port_default = False
                self.email_port_number = int(port)
            except: raise FetchmailExeption('Error in "port" specified')
        else:
            self.email_port_default = True
            self.email_port_number = ''
        self.folder_name = folder_name
        try:
            self.filters = filters
        except: raise FetchmailExeption('Error in "filters" provided. Must be list of [ Filter_object(), ... ]')
        self.delete_messages_flag = delete
        return self

class FetchmailExeption(Exception):
    """
    Special Exception to be raised by this library
    """
    pass