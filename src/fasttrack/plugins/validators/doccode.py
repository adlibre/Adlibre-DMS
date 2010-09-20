import re

from fileshare.utils import ValidatorProvider


class DocCode(ValidatorProvider):
    name = 'DocCode'
    description = '[A-Z]{3}[0-9]{8}'

    @staticmethod
    def validate(document):
        if re.match("^[A-Z]{3}[0-9]{8}$", document):
            return True
        return False

