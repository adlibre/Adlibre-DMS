# Adlibre DMS Installation and System Requirements

Adlibre DMS can be easily installed on any operating system provided that a recent copy of a Python interpreter is
available as well as any dependent system libraries.

## Linux Requirements

Installation under Linux is the most straight forward.

The following system libraries are required:

* Python 2.6 or 2.7
* libtiff
* poppler
* a2ps
* ghostscript == 8.X

Supported Linux Distributions:

* Debian
* Ubuntu
* CentOS / Red Hat.

## OS X Requirements

On OS X need the following will need to be installed using a 3rd party port / package manager.

You could, for example install the requirements using Mac Ports:

* http://www.macports.org/install.php

For 'magic' based file type validation we require the following:

    port install perl5
    port install p5-file-libmagic

and the following for converter.py to function (libtiff, poppler, a2ps, ghostscript)

    port install tiff
    port install poppler
    port install a2ps
    port install ghostscript

for a proper thumbnails generation we (thumbnails.py plugin) we require version of ghostscript:

    ghostscript == 8.X (tested with ghostscript 8.70)

## Windows Requirements

For commercial Windows installation support. Please enquire at http://www.adlibre.com.au/

## General Installation and Deployment

We recommend deployment with _virtualenv_:

You will need to specify Python version if more than one installed eg. --python /usr/bin/python2.6

Development:

    mkvirtualenv --no-site-packages dms
    workon dms
    cdvirtualenv
    pip install -e git+ssh://git@github.com/adlibre/Adlibre-DMS.git#egg=dms
    ./src/dms/adlibre_dms/manage.py syncdb
    ./src/dms/adlibre_dms/manage.py collectstatic
    ./src/dms/adlibre_dms/manage.py runserver

Production:

    mkvirtualenv --no-site-packages dms
    workon dms
    cdvirtualenv
    pip install git+git://github.com/adlibre/Adlibre-DMS.git
    ./adlibre_dms/manage.py syncdb
    ./adlibre_dms/manage.py collectstatic

Then setup your webserver to use a FastCGI socket.

See _deployment_ directory for sample webserver configs and a _manage-fcgi.sh_ script for managing the Python FCGI processes.

## Initial Data

We have provided some initial data (fixtures).

To use this data copy the fixtures and run _syncdb_:

    cp ./fixtures/test_initial_data.json ./fixtures/initial_data.json
    ./adlibredms_/manage.py syncdb

Output will be something like this:

    $ python manage.py syncdb
    Creating tables ...
    Installing custom SQL ...
    Installing indexes ...
    Installed 73 object(s) from 1 fixture(s)

It will mean you have sample initial data installed to your DB.

Sample initial data include superuser:

* login:     admin
* password:  admin

It is also a good idea would be to delete that copied ".json" file, just in case someone runs syncdb again.

Now you may add some test data to the system.
DMS has test files in "fixtures/testdata" directory.
You can run builtin "import_documents" command,
pointing out to this "testdata" directory.
It may look something like this:

    ./adlibre_dms/manage.py import_documents ../../fixtures/testdata/

This will populate documents folder with initial files,
imported by console command. You may run it several times to get
as much revisions, as you run the command.
