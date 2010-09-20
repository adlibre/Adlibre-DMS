from fileshare.utils import HashProvider


class MD5Hash(HashProvider):
    name = 'md5'

    @staticmethod
    def perform(document):
        return hashlib.md5(document).hexdigest()

