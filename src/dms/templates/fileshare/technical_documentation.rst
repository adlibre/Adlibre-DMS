
How to retrieve a document
==========================

1. List of document revisions

   ``http://example.com/revision/<document>``

2. Get file without active url-hash plugin

   ``http://example.com/get/<document>``

   or

   ``http://example.com/get/<document>.<extension>``

3. Get file with active url-hash plugin

   ``http://example.com/<hashcode>/<document>``

   or

   ``http://example.com/<hashcode>/<document>.<extension>``


Plugins
=======

Plugins are located in the plugins directory, and separated into 4 categories :

1. Doccode

2. Security

3. Storage

4. Validator

Common atributes in plugin :

**Please don't forget to give unique name to the
plugin.**


Atributes:
----------

*name*
    Name of the storage plugin


*description*
    Description of the plugin



Doccode
-------

Doccode is a rule identifier for matching the document name with the rule that
defines how the system processes the document. To create a new doccode, all you need to do is
to create new python class that inherits from DoccodeProvider and put the file in
the plugins doccode directory.

As shown in the example below, two methods need to be defined:

Sample
~~~~~~
::

    class DocCode(DocCodeProvider):
        name = 'DocCode-1'
        description = '[A-Z]{3}[0-9]{8}'

        @staticmethod
        def validate(document):
            if re.match("^[A-Z]{3}[0-9]{8}$", document):
                return True
            return False

        @staticmethod
        def split(document):
            d = [ document[0:3], document[3:11], ]
            return d

Security
--------

Security plugin is a type of plugin that handles the security aspect from
document system.

Methods:
~~~~~~~~
::

    def __init__(self):
        # set is_storing_action = True if it need to perform when saving file
        self.is_storing_action = True

        # set is_retrieval_action = True if it need to perform when retrieving file
        self.is_retrieval_action = True

        # default state for a plugin inside a rule
        self.active = True

    def perform(self, request, document):
        """Perform security check"""


Sample
~~~~~~
::

    class NotInSecurityGroupError(Exception):
        def __str__(self):
            return "NotInSecurityGroupError - You're not in security group"


    class security(SecurityProvider):
        name = 'Security Group'
        description = 'Security group member only'
        active = True

        def __init__(self):
            self.is_storing_action = True
            self.is_retrieval_action = True
            self.active = True

        def perform(self, request, document):
            security_group, created = Group.objects.get_or_create(name='security')
            if not security_group in request.user.groups.all():
                raise NotInSecurityGroupError


Storage
-------

Storage plugin is a type of plugin that handle how the file should be persisted.
It also should handle the revision system, revisions are intrinsically tied to
the underlying storage system.


Methods:
~~~~~~~~

::

    def store(filename):
    """Handle how the file saved in the storage"""

    def get(filename):
    """Get fullpath of a filename from storage"""

    def revision(document):
    """Get list of revision of a document"""


Sample
~~~~~~
::

    class Local(StorageProvider):
        name = "Local Storage"
        description = "Local storage plugin"

        @staticmethod
        def store(f, root = settings.DOCUMENT_ROOT):
            filename = f.name
            document, extension = os.path.splitext(filename)
            extension = extension.strip(".")
            directory = "%s/%s/%s" % (filename[0:3], filename[3:7], document)
            if root:
                directory = "%s/%s" % (root, directory)
            if not os.path.exists(directory):
                os.makedirs(directory)

            json_file = '%s/%s.json' % (directory, document)
            if os.path.exists(json_file):
                json_handler = open(json_file , mode='r+')
                fileinfo_db = json.load(json_handler)
                revision = fileinfo_db[-1]['revision'] + 1
            else:
                fileinfo_db = []
                revision = 1

            fileinfo = {
                'name' : "%s_r%s.%s" % (document, revision, extension),
                'revision' : revision,
                'created_date' : str(datetime.datetime.today())
            }
            fileinfo_db.append(fileinfo)
            json_handler = open(json_file, mode='w')
            json.dump(fileinfo_db, json_handler)

            destination = open('%s/%s' % (directory, fileinfo['name']), 'wb+')
            for chunk in f.chunks():
                destination.write(chunk)
            destination.close()


        @staticmethod
        def get(filename, root = settings.DOCUMENT_ROOT):
            document, extension = os.path.splitext(filename)
            extension = extension.strip(".")
            directory = "%s/%s/%s" % (document[0:3], document[3:7], document)
            if root:
                directory = "%s/%s" % (root, directory)

            json_file = '%s/%s.json' % (directory, document)
            if os.path.exists(json_file):
                json_handler = open(json_file , mode='r+')
                fileinfo_db = json.load(json_handler)
                fileinfo = fileinfo_db[-1]
            fullpath = '%s/%s' % (directory, fileinfo['name'])
            return fullpath


        @staticmethod
        def revision(document, root = settings.DOCUMENT_ROOT):
            directory = "%s/%s/%s" % (document[0:3], document[3:7], document)
            if root:
                directory = "%s/%s" % (root, directory)
            json_file = '%s/%s.json' % (directory, document)
            if os.path.exists(json_file):
                json_handler = open(json_file , mode='r+')
                fileinfo_db = json.load(json_handler)
                return fileinfo_db
            return None


Validator
---------
Validator is a plugin to handle validation of a file's contents.


Methods:
~~~~~~~~
::

    def __init__(self):
        # set is_storing_action = True if it need to perform when saving file
        self.is_storing_action = True

        # set is_retrieval_action = True if it need to perform when retrieving file
        self.is_retrieval_action = True

        # default state for a plugin inside a rule
        self.active = True

    def perform(self, request, document):
        """Perform validation again the document"""


Sample
~~~~~~
::

    class FileType(ValidatorProvider):
        name = 'File Type'
        description = 'File Type Validator'
        has_configuration = True


        def __init__(self):
            self.is_storing_action = True
            self.is_retrieval_action = False
            self.active = True
            self.available_type = []

        def perform(self, request, document):
            filebuffer=request.FILES['file']
            mime = magic.Magic(mime=True)
            if not mime.from_buffer(filebuffer.read()) in self.available_type:
                raise FileTypeError
            return True

