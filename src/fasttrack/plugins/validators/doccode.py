import re

from fileshare.utils import ValidatorProvider


class DocCode(ValidatorProvider):
    name = 'DocCode'

    @staticmethod
    def validate(document):
        if re.match("^[A-Z]{3}[0-9]{8}$", document):
            return True
        return False

