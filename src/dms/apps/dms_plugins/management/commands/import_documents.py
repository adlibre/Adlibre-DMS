import os
import traceback

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from document_manager import DocumentManager

class FakeRequest(object):
    def __init__(self):
        self.user = User.objects.filter(is_superuser = True)[0]

class Command(BaseCommand):
    args = '<directory_name directory_name ...>'
    help = 'Imports the documents from specified directory'

    def handle(self, *args, **options):

        if len(args) == 0:
            self.stdout.write('No arguments specified\n')
            return

        for directory in args:
            if not os.path.exists(directory):
                self.stderr.write('Could not import %s: no such directory\n' % directory)
                continue
            cnt = 0
            manager = DocumentManager()
            for root, dirs, files in os.walk(directory):
                if '.svn' in dirs:
                    dirs.remove('.svn')  # don't visit svn directories
                for fil in files:
                    file_obj = open(os.path.join(root, fil))
                    file_obj.seek(0)
                    try:
                        manager.store(FakeRequest(), file_obj)
                    except:
                        self.stderr.write(traceback.format_exc() + "\n")
                    else:
                        if manager.errors:
                            self.stderr.write("\n".join(map(lambda x: x[0], manager.errors)) + "\n")
                        else:
                            cnt += 1
                    file_obj.close()
            if cnt:
                self.stdout.write('Successfully imported %s documents from directory "%s"\n' % (cnt, directory))
            else:
                self.stdout.write('No documents were imported\n')
