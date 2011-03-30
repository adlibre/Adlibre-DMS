import re
from browser.utils import DocCodeProvider


class DocCode(DocCodeProvider):
    
    name = 'Fax Tiff Documents'
    description = '[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{1,9}'

    @staticmethod
    def validate(document):
        if re.match("^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{1,9}$", document):
            return True
        return False

    @staticmethod
    def split(document):
        d = [ document[0:4], document[5:7], document[8:10], document[11:20]]
        return d
