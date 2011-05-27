from django.contrib.auth.models import Group

from dms_plugins.workers import PluginError

class NotInSecurityGroupError(PluginError):
    def __str__(self):
        return "NotInSecurityGroupError - You're not in security group"

class GroupSecurityWorker(object):
    def work(self, request, document, **kwargs):
        security_group, created = Group.objects.get_or_create(name='security')
        if not security_group in request.user.groups.all():
            raise PluginError("You're not in security group")
        return document