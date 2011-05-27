from django.conf import settings
from dms_plugins.workers import PluginError

class HashCodeValidator(object):
    method = 'md5'

    def get_hash(self, document):
        salt = settings.SECRET_KEY
        h = hashlib.new(self.method)
        h.update(document)
        h.update(salt)
        return h.hexdigest()

    def work(self, request, document):
        hashcode = document.get_hashcode()
        if hashcode and not (self.get_hash == hashcode):
            raise PluginError("Hashcode did not validate.")
        return document

#TODO: migrate plugin settings