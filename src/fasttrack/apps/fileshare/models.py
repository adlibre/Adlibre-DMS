import os
import hashlib

from django.db import models

class FileShare(models.Model):
    hashcode = models.CharField(max_length=50, editable=False)
    sharefile = models.FileField(upload_to='files', max_length=255)
    
    def __unicode__(self):
        return "%s" % os.path.basename(self.sharefile.file.name)
    
    def save(self, *args, **kwargs):
        filename = os.path.basename(self.sharefile.file.name)
        self.hashcode = hashlib.md5(filename).hexdigest()        
        super(FileShare, self).save(*args, **kwargs)
        
    @models.permalink
    def get_absolute_url(self):
        return ('get_file', [self.hashcode, os.path.basename(self.sharefile.file.name)])
        
