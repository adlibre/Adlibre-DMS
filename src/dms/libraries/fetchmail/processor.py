"""
Fetchmail library for Adlibre DMS

Processor Module
Role: Handles ready and downloaded message. 
It does In memory message processing and saves attachments to directory,
specified in settings

Author: Iurii Garmash (garmon1@gmail.com)
"""

import email, os
from libraries.fetchmail.app_settings import STORE_FILES_PATH, FILENAME_EXISTS_CHANGE_SYMBOL

def process_single_letter(msg, filter_filename=False, quiet=False):
    """
    Processing single message.
    Takes message instance ('msg' must be an RFC822 formatted message.)
    Scans for attachments and saves them to temporary folder.
    Returns file list.
    """
    # different approaches here.
    # trying to read IMAP4 message first otherwise treating it like POP3
    try:
        message = email.message_from_string(str(msg[0][1]))
    except:
        message = email.message_from_string(str(msg))
    filenames = []
    for part in message.walk():
        #print (part.as_string() + "\n")
        # multipart/* are just containers
        if part.get_content_maintype() == 'multipart':
            continue
        filename = part.get_filename()
        if filename:
            # checking if 'filename' filter applied and omitting save sequence 
            # in case file's name does not contain this string
            # TODO: HACK! a bit of a hack here. maybe change it in future
            if filter_filename:
                if filename.rfind(filter_filename) != -1:
                #if not filename == filter_filename:
                    pass
                else:
                    continue
            if not quiet:
                print ("Fetched filename:"+ str(filename));
            # cycle file existence check/renaming sequence
            file_exists = os.path.isfile(os.path.join(STORE_FILES_PATH, filename))
            if file_exists:
                if not quiet:
                    print 'File already exists: '+str(filename)
                new_file_exists = True
                new_filename = filename
                while new_file_exists:
                    directory, filename = os.path.split(new_filename)
                    filename_string, extension = os.path.splitext(new_filename)
                    new_filename_string = filename_string + FILENAME_EXISTS_CHANGE_SYMBOL
                    new_filename = new_filename_string + extension
                    new_file_exists = os.path.isfile(os.path.join(STORE_FILES_PATH, new_filename))
                filename = new_filename
                if not quiet:
                    print 'Renamed to: ' + str(filename)
            fp = open(os.path.join(STORE_FILES_PATH, filename), 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()
            filenames += [filename]
    return filenames
