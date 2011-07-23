import re

from doc_codes import Doccode

class CreditCardDoccode(Doccode):
    """
    Example DocCode: Store document_names that are indexed by credit card number. NB, this is not recommended,
    but it demonstrates more complex validation is possible.
    """

    title = 'Credit Card Scans'
    description = '[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}'
    active = True
    doccode_id = 5

    def validate(self, document_name):

        cc = document_name[0:4] + document_name[5:9] + document_name[10:13] + document_name[14:18]

        if re.match("^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$", document_name) and self.is_luhn_valid(cc):
            return True
        return False

    def split(self, document_name):
        d = [ document_name[0:4], document_name[5:9], document_name[10:13], document_name[14:18], document_name ]
        return d

    # Credit: http://en.wikipedia.org/wiki/Luhn_algorithm
    def is_luhn_valid(self, cc):
        num = [int(x) for x in str(cc)]
        return sum(num[::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0
