from fileshare.utils import ValidatorProvider


class filetype(ValidatorProvider):
    name = 'File Type'
    description = 'File Type Validator'
    active = True

    @staticmethod
    def perform(request):
        return True

