from django.db.models.signals import post_syncdb

from djangoplugins import models as plugins_app
from djangoplugins.management import sync_plugins

post_syncdb.disconnect(sync_plugins, sender=plugins_app)
