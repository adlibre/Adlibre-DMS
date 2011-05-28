from django.conf import settings

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint
from dms_plugins.workers import Plugin, PluginError

class HashCodeValidationPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = 'Hash'
    description = 'Hash code validation on retrieval'
    active = True

    method = 'md5'
    has_configuration = True #TODO: configuration

    def get_hash(self, document, salt = settings.SECRET_KEY):
        h = hashlib.new(self.method)
        h.update(document)
        h.update(salt)
        return h.hexdigest()

    def work(self, request, document):
        hashcode = document.get_hashcode()
        if hashcode and not (self.get_hash == hashcode):
            raise PluginError("Hashcode did not validate.")
        return document
