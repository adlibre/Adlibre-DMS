"""
Module: DMS Thumbnails Local Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""
from wand.image import Image
from subprocess import call

import os

from dms_plugins.workers.storage.local import LocalFilesystemManager

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint
from dms_plugins.workers import Plugin


class ThumbnailsLocalRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):

    title = "Thumbnails Handler"
    description = "Makes thumbnails of an image and returns it if necessary"
    plugin_type = "retrieval_processing"

    def work(self, document):
        return ThumbnailsFilesystemHandler().retrieve_thumbnail(document)


class ThumbnailsFilesystemHandler(object):
    """Implements loading of thumbnails Lazily.

    E.g. Thumbnail will be generated on first call"""

    def __init__(self):
        self.filesystem = LocalFilesystemManager()
        self.thumbnail_folder = 'thumbnails_storage'

    def retrieve_thumbnail(self, document):
        """Handles retrieval of thumbnail and optional generation of it"""
        print document
        code_dir = self.filesystem.get_or_create_document_directory(document)
        print code_dir
        thumbnail_directory = os.path.join(code_dir, self.thumbnail_folder)

        thumbnail_location = os.path.join(thumbnail_directory, document.get_full_filename())
        # if os.path.exists(thumbnail_location):
        #     document.thumbnail = open(thumbnail_location).read()
        # else:
        document.thumbnail = self.generate_thumbnail(document, thumbnail_location, thumbnail_directory)

        return document

    def generate_thumbnail(self, document, thumbnail_location, thumbnail_directory):
        """Generating a thumbnail based on document first file"""
        print thumbnail_location
        print document.get_file_obj()
        try:
            if not os.path.exists(thumbnail_directory):
                os.makedirs(thumbnail_directory)
            # Storing temporary PDF file for converting
            tmp_pdf = open(thumbnail_location, 'w')
            tmp_pdf.write(document.get_file_obj().read())
            tmp_pdf.close()

            file_page = os.path.normpath(thumbnail_location)
            print file_page
            # from subprocess import call
            # call(['gs', file_page])
            call([
                'gs',
                '-q',
                '-dSAFER',
                '-sDEVICE=png16m',
                '-r500',
                '-dBATCH',
                '-dNOPAUSE',
                '-dFirstPage=1',
                '-dLastPage=1'
                '-sOutputFile=%s.png' % file_page,
                file_page
            ])
            thumbnail_png = file_page + '.png'
            with Image(filename=file_page) as img:
                print img.width
                print 'executed'
        except Exception, e:
            print e
            pass

        return open(thumbnail_location).read()
