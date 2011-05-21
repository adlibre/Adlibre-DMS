class Doccode(object):
    def get_id(self):
        return self.doccode_id

    def get_title(self):
        title = getattr(self, 'title', '')
        if not title:
            title = getattr(self, 'name', '')
        return title