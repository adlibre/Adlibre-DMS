from django.contrib.auth.models import Group
from django.db.models import signals

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint
from dms_plugins.workers import Plugin, PluginError

SECURITY_GROUP_NAME = 'security'


class GroupSecurityStore(Plugin, BeforeStoragePluginPoint):
    title = 'Security Group on storage'
    description = 'Security group member only [storage]'
    plugin_type = 'security'

    def work(self, document):
        return GroupSecurity().work(document)


class GroupSecurityRetrieval(Plugin, BeforeRetrievalPluginPoint):
    title = 'Security Group on retrieval'
    description = 'Security group member only [retrieval]'
    plugin_type = 'security'

    def work(self, document):
        return GroupSecurity().work(document)


class GroupSecurityRemoval(Plugin, BeforeRemovalPluginPoint):
    title = 'Security Group on removal'
    description = 'Security group member only [removal]'
    plugin_type = 'security'

    def work(self, document):
        return GroupSecurity().work(document)


class GroupSecurity(object):
    def work(self, document):
        user = document.user
        if not user:
            raise PluginError("Not a logged in user.", 403)
        security_group, created = Group.objects.get_or_create(name=SECURITY_GROUP_NAME)
        if not security_group in user.groups.all() and not user.is_superuser:
            raise PluginError("You're not in %s group" % SECURITY_GROUP_NAME, 403)
        return document


def create_security_group(**kwargs):
    """Create user groups required for processing of security in MUI"""
    Group.objects.get_or_create(name=SECURITY_GROUP_NAME)

# Attached this to recreate group for each syncdb
signals.post_syncdb.connect(create_security_group)