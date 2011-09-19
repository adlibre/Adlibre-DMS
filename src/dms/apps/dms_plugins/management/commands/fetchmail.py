# Mail management script for Adlibre DMS
#
# - Authenticates with IMAP4/POP3 protocols
# - Searches mailbox for messages based on provided filters
# - Saves attachments to temporary folder
# - Default settings stored in libraries/fetchmail/app_settings.py
#
# Author: Iurii Garmash (garmon1@gmail.com)

from django.core.management.base import BaseCommand
from libraries.fetchmail.fetchmail_lib import process_email
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
        response = process_email(quiet=quiet)
        if not quiet:
            self.stdout.write(str(response))
            self.stdout.write('\n')
        

