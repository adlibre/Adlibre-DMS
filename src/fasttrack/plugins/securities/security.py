from django.contrib.auth.models import Group

from fileshare.utils import SecurityProvider


class security(SecurityProvider):
    name = 'Security Group'
    description = 'Security group member only'
    active = True

    def __init__(self):
        self.is_storing_action = True
        self.is_retrieval_action = True
        self.active = True

    @staticmethod
    def perform(request, document):
        try:
            security_group = Group.objects.get(name='security')
        except:
            return False
        if security_group in request.user.groups.all():
            return True
        return False

