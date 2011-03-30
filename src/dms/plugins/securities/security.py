from django.contrib.auth.models import Group

from browser.utils import SecurityProvider


class NotInSecurityGroupError(Exception):
    def __str__(self):
        return "NotInSecurityGroupError - You're not in security group"


class Security(SecurityProvider):
    name = 'Security Group'
    description = 'Security group member only'
    active = True

    def __init__(self):
        self.is_storing_action = True
        self.is_retrieval_action = True
        self.active = True

    def perform(self, request, document):
        security_group, created = Group.objects.get_or_create(name='security')
        if not security_group in request.user.groups.all():
            raise NotInSecurityGroupError

