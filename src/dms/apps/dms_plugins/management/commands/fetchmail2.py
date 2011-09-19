# Mail management script for Adlibre DMS
#
# Example usage of "fetchmail" library.
# must be run under full access privileges to write files
#
# Author: Iurii Garmash (garmon1@gmail.com)

from django.core.management.base import BaseCommand
from libraries.fetchmail.models import Fetcher_object, Email_object, Filter_object
from optparse import make_option

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
    help = "Fetches mail from IMAP/POP3 server and saves attachments to temporary directory"
    
    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        if not quiet:
            self.stdout.write('Starting to process e-mails')
        
        # creating filters objects first
        email_filter1 = Filter_object()
        email_filter2 = Filter_object()
        email_filter1 = email_filter1.create_filter(filter_type='sender', value='Iurii')
        email_filter2 = email_filter2.create_filter(filter_type='subject', value='test message 3')
        # creating email object with this filters
        email = Email_object()
        email = email.create_email(server_name='imap.gmail.com',
                                   login='adlibre.dms.test',
                                   password='adlibre_dms_test_password',
                                   filters = [email_filter1, email_filter2])
        # processing mail with Fetcher() instance
        fetcher = Fetcher_object()
        fetcher.fetchmail(email=email, quiet=quiet)
        if not quiet:
            self.stdout.write('Fetching completed successfully!')
            self.stdout.write('\n')
        

