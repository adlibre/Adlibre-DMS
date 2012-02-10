from datetime import datetime
from django.db import models

from couchdbkit.ext.django.schema import *

class CouchDocument(Document):
    author = StringProperty()
    date = DateTimeProperty(default=datetime.utcnow)

    class Meta:
        app_label = "dmscouch"