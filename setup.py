#!/usr/bin/env python

import os
import fnmatch

from setuptools import setup, find_packages

def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for base_name in files:
            if fnmatch.fnmatch(base_name, pattern):
                filename = os.path.join(root, base_name)
                if os.path.isfile(filename):
                    yield filename

def find_files_full(dir, pattern='*'):
    """
    Returns a dict with full relative path to files
    """
    all_files = []
    for root, dirs, files in os.walk(dir):
        if len(files) > 0:
            for file in fnmatch.filter(files, pattern):
                file_path = os.path.join(root, file)
                all_files.extend((file_path,))
    return all_files

def findall(dir, pattern='*'):
    """
    A better finder for 'data_files'
    """
    all_files = []
    for root, dirs, files in os.walk(dir):
        if len(files) > 0:
            file_list = []
            for file in fnmatch.filter(files, pattern):
                file_path = os.path.join(root, file)
                file_list.extend((file_path,))
            all_files.extend(((root, file_list,),))
    return all_files


setup(name='adlibre_dms',
    version=open('version.txt').read(),
    long_description=open('README.md').read(),
    url='https://github.com/adlibre/Adlibre-DMS',
    packages=find_packages('.'),
    scripts=[],
    package_data={
            'adlibre_dms': [
		        'version.txt',
                'apps/browser/static/favicon.ico',
                'apps/browser/static/browser/*',
                'apps/browser/templates/browser/*.html',
                'apps/browser/templates/browser/include/*.html',
                'apps/docs/templates/docs/*',
                'apps/mdtui/*.pdf',
                'apps/mdtui/static/*.ico',
                'apps/mdtui/static/*.png',
                'apps/mdtui/static/css/*.css',
                'apps/mdtui/static/img/*.png',
                'apps/mdtui/static/js/*.js',
                'apps/mdtui/templates/mdtui/*.html',
                # Themes
                'apps/theme/*/static/theme/*/*.png',
                'apps/theme/*/static/theme/*/*.css',
                'apps/theme/*/templates/*/*.html',
                # Admin UI
                'apps/ui/static/css/ui/*.css',
                'apps/ui/static/css/ui/datepick/*.css',
                'apps/ui/templates/ui/*.html',
                # CouchDB Components
                'couchapps/*/_design/views/*/*.js',

                'libraries/piston/templates/*.html',
                'libraries/piston/templates/piston/*.html',

                # Misc templates
                'templates/*.html',
                'templates/*.txt',
                'templates/admin/*.html',
                'templates/flatpages/*.html',
                'templates/registration/*.html',

                ], # this should be done automatically
        },
    data_files=[
        ('adlibre_dms', ['settings_prod.py', 'local_settings.py.example', 'adlibre_dms/manage.py']),
        ('db', ['db/.gitignore']), # create empty dir
        ('deployment', find_files('deployment', '*')),
        ('log', ['log/.gitignore']), # create empty dir
        ('www', ['www/.gitignore']), # create empty dir
        ('www/status-pages', ['www/status-pages/500.html', 'www/status-pages/503.html']),
    ],
    install_requires=[
            # Core requirements
            'Django==1.3.1',
            'python-magic==0.4.2',
            'django-compressor==1.1.2',
            'docutils==0.7',
            # MUI
            'couchdbkit==0.6.1',
            'django-widget-tweaks==1.0',
            # Tagging
            'django-taggit==0.9.3',
            # Adlibre Components
            'django-bcp',
            'adlibre-plugins',
            # not sure if we directly require these
            'distribute==0.6.25',
            'django-appconf==0.5',
            'http-parser==0.7.4',
            'pyPdf==1.13',
            # Deployment
            'flup==1.0.3.dev-20110405',
        ],
    dependency_links = [
        "https://github.com/adlibre/django-bcp/tarball/master#egg=django-bcp",
        "https://github.com/adlibre/adlibre-plugins/tarball/master#egg=adlibre-plugins"
    ],
)


