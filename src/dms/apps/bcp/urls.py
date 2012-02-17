"""
Module: Barcode Printer URLS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.simple import redirect_to

import mdtui.views

urlpatterns = patterns('bcp.views',
    url(r'^(?P<barcode_type>[\d\w]+)/(?P<code>.+)$', 'generate', name='bcp-generate'),
)