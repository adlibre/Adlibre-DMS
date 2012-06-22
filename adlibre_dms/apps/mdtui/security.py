"""
Module: DMS MUI security handlers module

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals

from doc_codes.models import DocumentTypeRule

SEC_GROUP_NAMES = {
    'search': 'MUI Search interaction',
    'index': 'MUI Index interaction'
}

def update_docrules_permissions(**kwargs):
    """Triggering programmatic save() of each DocumentTypeRule on syncdb to generate permission for each DocumentTypeRule"""
    docrules = DocumentTypeRule.objects.all()
    for rule in docrules:
        rule.save()
        #print 'Created user role/permission for each DocumentTypeRule()'

def cleanup_docrules_permissions(**kwargs):
    """Cleans up all permissions for each DocumentTypeRule()"""
    content_type, created = ContentType.objects.get_or_create(app_label='rule', model='', name='document type')
    permissions = Permission.objects.filter(content_type=content_type)
    for p in permissions:
        p.delete()
        #print 'Deleted all permissions for each DocumentTypeRule()'

def create_groups(**kwargs):
    """Create user groups required for processing of security in MUI"""
    for gname in SEC_GROUP_NAMES.itervalues():
        g = Group.objects.get_or_create(name=gname)

# Attached this to recreate permissions for each syncdb
signals.post_syncdb.connect(update_docrules_permissions)
signals.post_syncdb.connect(create_groups)