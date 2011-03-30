import re
from browser.utils import DocCodeProvider


class DocCode(DocCodeProvider):
    """
    Example DocCode: Store documents that are indexed by credit card number. NB, this is not recommended,
    but it demonstrates more complex validation is possible.
    """

    name = 'Credit Card Scans'
    description = '[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}'

    @staticmethod
    def validate(document):

        cc = document[0:4] + document[5:9] + document[10:13] + document[14:18]

        if re.match("^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$", document) and self.is_luhn_valid(cc):
            return True
        return False

    @staticmethod
    def split(document):
        d = [ document[0:4], document[5:9], document[10:13], document[14:18] ]
        return d

    # Credit: http://en.wikipedia.org/wiki/Luhn_algorithm
    @staticmethod
    def is_luhn_valid(cc):
        num = [int(x) for x in str(cc)]
        return sum(num[::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0
