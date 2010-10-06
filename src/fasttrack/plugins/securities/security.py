from django.contrib.auth.models import Group

from fileshare.utils import SecurityProvider


class security(SecurityProvider):
    name = 'Security Group'
    active = True

    @staticmethod
    def perform(request):
        security_group = Group.objects.get(name='security')
        if security_group in request.user.groups.all():
            return True
        return False

