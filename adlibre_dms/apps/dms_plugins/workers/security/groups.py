from django.contrib.auth.models import Group

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint
from dms_plugins.workers import Plugin, PluginError

class GroupSecurityStore(Plugin, BeforeStoragePluginPoint):
    title = 'Security Group on storage'
    description = 'Security group member only [storage]'
    plugin_type = 'security'

    def work(self, user, document):
        return GroupSecurity().work(user, document)

class GroupSecurityRetrieval(Plugin, BeforeRetrievalPluginPoint):
    title = 'Security Group on retrieval'
    description = 'Security group member only [retrieval]'
    plugin_type = 'security'

    def work(self, user, document):
        return GroupSecurity().work(user, document)

class GroupSecurityRemoval(Plugin, BeforeRemovalPluginPoint):
    title = 'Security Group on removal'
    description = 'Security group member only [removal]'
    plugin_type = 'security'

    def work(self, user, document):
        return GroupSecurity().work(user, document)

class GroupSecurity(object):
    def work(self, user, document, **kwargs):
        security_group, created = Group.objects.get_or_create(name='security')
        if not security_group in user.groups.all():
            raise PluginError("You're not in security group", 403)
        return document
