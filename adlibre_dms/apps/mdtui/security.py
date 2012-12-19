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
    'index': 'MUI Index interaction',
    'edit_index': 'MUI can Edit Document Indexes',
    'edit_fixed_indexes': 'MUI Edit fixed choice indexes',
}


def list_permitted_docrules_qs(user):
    """
    Returns QuerySet of all user permitted Document Tyrpe Rules.

    Usually we need to check if user is superuser and/or staff before calling this.
    """
    # Filtering Document Type Rules for user
    perms = user.user_permissions.all()
    allowed_docrules_names = []
    # Checking for permitted docrules
    for permission in perms:
        if permission.content_type.name=='document type':
            if not permission.codename in allowed_docrules_names:
                allowed_docrules_names.append(permission.codename)
    for group in user.groups.all():
        for permission in group.permissions.all():
            if permission.content_type.name=='document type':
                if not permission.codename in allowed_docrules_names:
                    allowed_docrules_names.append(permission.codename)
    docrules_queryset = DocumentTypeRule.objects.filter(title__in=allowed_docrules_names)
    return docrules_queryset

def list_permitted_docrules_pks(user):
    """
    Returns list of all, permissions enabled only, user Document Type Rule PK's.

    Usually need to check if user is superuser and/or staff before calling this.
    """
    docrules_queryset = list_permitted_docrules_qs(user)
    # Getting list of PKs of allowed Document Type Rules.
    allowed_docrules_pks = []
    if docrules_queryset:
        for rule in docrules_queryset:
            allowed_docrules_pks.append(unicode(rule.pk))
    return allowed_docrules_pks

def filter_permitted_docrules(docrules_list, user):
    """
    Filteres docrule list according to user permissions to access that docrule.
    """
    result = []
    allowed_docrule_pks = list_permitted_docrules_pks(user)
    for docrule in docrules_list:
        if docrule in allowed_docrule_pks:
            result.append(docrule)
    return result

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