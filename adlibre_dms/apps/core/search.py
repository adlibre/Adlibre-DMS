"""test"""


class SearchQuery(object):
    """Defined data to be queried from DMS Search Manager class"""

    def __init__(self):
        self.document_keys = None

class SearchResults(object):
    """Defines data to be ruturned by DMS Search Manager class"""
    def __init__(self):
        self.documents = None