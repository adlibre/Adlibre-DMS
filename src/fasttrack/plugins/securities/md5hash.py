from fileshare.utils import SecurityProvider


class MD5Hash(SecurityProvider):
    name = 'md5'
    active = True
    plugin_type = 'hash'

    @staticmethod
    def perform(document):
        return hashlib.md5(document).hexdigest()

