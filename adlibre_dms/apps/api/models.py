from django.contrib.auth.models import Group
from django.db.models import signals

API_GROUP_NAME = 'api'


def create_api_group(**kwargs):
    """Create user group required for processing of security in API"""
    Group.objects.get_or_create(name=API_GROUP_NAME)

# Attached this to recreate group for each syncdb
signals.post_syncdb.connect(create_api_group)