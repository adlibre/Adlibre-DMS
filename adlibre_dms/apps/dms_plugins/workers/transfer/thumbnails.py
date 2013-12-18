"""
Module: DMS Thumbnails Local Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""
import os
import shutil
import ghostscript
import logging

from PIL import Image

from dms_plugins.workers.storage.local import LocalFilesystemManager

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint, BeforeUpdatePluginPoint
from dms_plugins.workers import Plugin, PluginError

log = logging.getLogger('dms')


class ThumbnailsFilesystemHandler(object):
    """Handles a thumbnails interaction

    Implemented in a lazy way.
    Thumbnail is created on first request
    and stored for farther usage afterwards withing that code directory
    """

    def __init__(self):
        self.filesystem = LocalFilesystemManager()
        self.thumbnail_folder = 'thumbnails_storage'
        self.jpeg_size = 64, 64  # px, px (pixels size - width, height)

    def retrieve_thumbnail(self, document):
        """Handles retrieval of thumbnail and optional generation of it"""
        thumbnail_location, thumbnail_directory = self.get_thumbnail_path(document)
        if not os.path.exists(thumbnail_location + '.png'):
            # TODO: remove this try/except block and stabilize
            # Operations are not stable due to plugin usage of external tools that are under testing now
            try:
                # To write a mimetype thumbnail handler add similar code  and create your function
                log.debug('mimetype for thumbnail: %s' % document.mimetype)
                if not document.mimetype:
                    raise PluginError('ThumbnailsFilesystemHandler missconfiguration. Mimetype = None', 404)
                if document.mimetype == 'application/pdf':
                    self.generate_thumbnail_from_pdf(document)
                if document.mimetype == 'image/jpeg':
                    self.generate_thumbnail_from_jpeg(document)
                document.thumbnail = open(thumbnail_location + '.png').read()
            except Exception, e:
                error = 'ThumbnailsFilesystemHandler.generate_thumbnail method error: %s' % e
                log.error(error)
                raise PluginError(error, 404)
        else:
            document.thumbnail = open(thumbnail_location + '.png').read()
        return document

    def remove_thumbnail(self, document):
        """Removes existing thumbnails path along with all files inside it"""
        thumbnail_location, thumbnail_directory = self.get_thumbnail_path(document, filename=False)
        if os.path.isdir(thumbnail_directory):
            shutil.rmtree(thumbnail_directory)
        return document

    # ******************************************************************************************************************
    # ****************************************** Helper methods (Internal) *********************************************
    # ******************************************************************************************************************

    def generate_thumbnail_from_pdf(self, document):
        """Generating a thumbnail based on document first file"""
        thumbnail_temporary, thumbnail_directory = self.get_thumbnail_path(document)
        # Creating directory for thumbnail if not exists
        if not os.path.exists(thumbnail_directory):
            os.makedirs(thumbnail_directory)
        # Storing temporary PDF file for converting
        tmp_pdf = open(thumbnail_temporary, 'w')
        tmp_pdf.write(document.get_file_obj().read())
        tmp_pdf.close()
        args = [
            'gs',
            '-q',  # Quiet
            '-dSAFER',
            '-sDEVICE=png16m',  # Type. PNG used
            '-r10',  # resolution of the thumbnail
            '-dBATCH',  # Quit GS after converting
            '-dNOPAUSE',  # Do not stop on pages
            '-dFirstPage=1',
            '-dLastPage=1',
            '-sOutputFile=%s.png' % thumbnail_temporary,  # Destination
            '%s' % thumbnail_temporary,  # Source
        ]
        ghostscript.Ghostscript(*args)
        # Deleting the temp PDF
        os.unlink(thumbnail_temporary)

    def generate_thumbnail_from_jpeg(self, document):
        """Generating a thumbnail based on document first file"""
        # Raising exception in case requiring to generate a thumbnail and Image module is not supported by virtualenv
        thumbnail_temporary, thumbnail_directory = self.get_thumbnail_path(document)
        # Creating directory for thumbnail if not exists
        if not os.path.exists(thumbnail_directory):
            os.makedirs(thumbnail_directory)
        log.debug('generate_thumbnail_from_jpeg attempt with Pillow')
        try:
            im = Image.open(document.get_file_obj())
            im.thumbnail(self.jpeg_size, Image.ANTIALIAS)
            im.save(thumbnail_temporary + '.png', "PNG")
        except Exception, e:
            log.error('generate_thumbnail_from_jpeg error: %s' % e)
            pass

    def get_thumbnail_path(self, document, filename=True):
        """Produces 2 path of tmp thumbnail file and a directory for thumbnails storage"""
        # Support for old docrule
        new_filename = None
        new_docrule = None
        if document.old_docrule:
            new_filename = document.file_name
            new_docrule = document.docrule
            document.set_filename(document.old_name_code)
            document.docrule = document.old_docrule
        code_dir = self.filesystem.get_or_create_document_directory(document)
        thumbnail_directory = os.path.normpath(os.path.join(code_dir, self.thumbnail_folder))
        thumbnail_temporary = None

        if filename:
            thumbnail_temporary = os.path.normpath(os.path.join(thumbnail_directory, document.get_full_filename()))
        if document.old_docrule:
            document.file_name = new_filename
            document.docrule = new_docrule
        return thumbnail_temporary, thumbnail_directory


class ThumbnailsLocalRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):

    title = "Thumbnails Handler"
    description = "Makes thumbnails of an image and returns it if necessary"
    plugin_type = "retrieval_processing"

    def work(self, document):
        if 'thumbnail' in document.options and document.options['thumbnail']:
            document = ThumbnailsFilesystemHandler().retrieve_thumbnail(document)
        return document


class ThumbnailsLocalRemovalPlugin(Plugin, BeforeRemovalPluginPoint):

    title = "Thumbnails Handler"
    description = "Removes thumbnails of the document"
    plugin_type = "retrieval_processing"

    def work(self, document):
        return ThumbnailsFilesystemHandler().remove_thumbnail(document)


class ThumbnailsLocalUpdatePlugin(Plugin, BeforeUpdatePluginPoint):

    title = "Thumbnails Handler"
    description = "Removes thumbnails of the document"
    plugin_type = "retrieval_processing"

    def work(self, document):
        return ThumbnailsFilesystemHandler().remove_thumbnail(document)
