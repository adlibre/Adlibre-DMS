"""
Module: DMS Browser Main data handlers

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""
from django.contrib.auth.models import Group
from django.db.models import signals


def create_aui_permissions(**kwargs):
    """Creates all permissions for AUI interaction"""
    group_name = 'AUI Interact'
    Group.objects.get_or_create(name=group_name)

# Attached this to recreate permissions for each syncdb
signals.post_syncdb.connect(create_aui_permissions)