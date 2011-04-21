import re
from base.utils import DocCodeProvider


class DocCode(DocCodeProvider):

    name = 'Project Gutenberg eBooks'
    description = '[0-9]{1,6}'

    @staticmethod
    def validate(document):
        if re.match('^[0-9]{1,6}$', document):
            return True
        else:
            return False

    # Split document as per Project Gutenberg method for 'eBook number' not, eText
    # http://www.gutenberg.org/dirs/00README.TXT
    @staticmethod
    def split(document):
        d = []
        for i in range(len(document)):
            d.append(document[i-1:i])
        return d
