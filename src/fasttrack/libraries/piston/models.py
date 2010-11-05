import urllib
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.conf import settings
from django.core.mail import send_mail, mail_admins
from django.template import loader

from managers import TokenManager, ConsumerManager, ResourceManager

KEY_SIZE = 18
SECRET_SIZE = 32

CONSUMER_STATES = (
    ('pending', 'Pending approval'),
    ('accepted', 'Accepted'),
    ('canceled', 'Canceled'),
)

class Nonce(models.Model):
    token_key = models.CharField(max_length=KEY_SIZE)
    consumer_key = models.CharField(max_length=KEY_SIZE)
    key = models.CharField(max_length=255)
    
    def __unicode__(self):
        return u"Nonce %s for %s" % (self.key, self.consumer_key)

admin.site.register(Nonce)

class Resource(models.Model):
    name = models.CharField(max_length=255)
    url = models.TextField(max_length=2047)
    is_readonly = models.BooleanField(default=True)
    
    objects = ResourceManager()

    def __unicode__(self):
        return u"Resource %s with url %s" % (self.name, self.url)

admin.site.register(Resource)

class Consumer(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    key = models.CharField(max_length=KEY_SIZE)
    secret = models.CharField(max_length=SECRET_SIZE)

    status = models.CharField(max_length=16, choices=CONSUMER_STATES, default='pending')
    user = models.ForeignKey(User, null=True, blank=True, related_name='consumers')

    objects = ConsumerManager()
        
    def __unicode__(self):
        return u"Consumer %s with key %s" % (self.name, self.key)

    def generate_random_codes(self):
        key = User.objects.make_random_password(length=KEY_SIZE)

        secret = User.objects.make_random_password(length=SECRET_SIZE)

        while Consumer.objects.filter(key__exact=key, secret__exact=secret).count():
            secret = User.objects.make_random_password(length=SECRET_SIZE)

        self.key = key
        self.secret = secret
        self.save()

    # -- 
    
    def save(self, **kwargs):
        super(Consumer, self).save(**kwargs)
        
        if self.id and self.user:
            subject = "API Consumer"
            rcpt = [ self.user.email, ]

            if self.status == "accepted":
                template = "api/mails/consumer_accepted.txt"
                subject += " was accepted!"
            elif self.status == "canceled":
                template = "api/mails/consumer_canceled.txt"
                subject += " has been canceled"
            else:
                template = "api/mails/consumer_pending.txt"
                subject += " application received"
                
                for admin in settings.ADMINS:
                    bcc.append(admin[1])

            body = loader.render_to_string(template, 
                    { 'consumer': self, 'user': self.user })
                    
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, 
                        rcpt, fail_silently=True)
            
            if self.status == 'pending':
                mail_admins(subject, body, fail_silently=True)
                        
            if settings.DEBUG:
                print "Mail being sent, to=%s" % rcpt
                print "Subject: %s" % subject
                print body

admin.site.register(Consumer)

class Token(models.Model):
    REQUEST = 1
    ACCESS = 2
    TOKEN_TYPES = ((REQUEST, u'Request'), (ACCESS, u'Access'))
    
    key = models.CharField(max_length=KEY_SIZE)
    secret = models.CharField(max_length=SECRET_SIZE)
    token_type = models.IntegerField(choices=TOKEN_TYPES)
    timestamp = models.IntegerField()
    is_approved = models.BooleanField(default=False)
    
    user = models.ForeignKey(User, null=True, blank=True, related_name='tokens')
    consumer = models.ForeignKey(Consumer)
    
    objects = TokenManager()
    
    def __unicode__(self):
        return u"%s Token %s for %s" % (self.get_token_type_display(), self.key, self.consumer)

    def to_string(self, only_key=False):
        token_dict = {
            'oauth_token': self.key, 
            'oauth_token_secret': self.secret
        }
        if only_key:
            del token_dict['oauth_token_secret']
        return urllib.urlencode(token_dict)

    def generate_random_codes(self):
        key = User.objects.make_random_password(length=KEY_SIZE)
        secret = User.objects.make_random_password(length=SECRET_SIZE)

        while Token.objects.filter(key__exact=key, secret__exact=secret).count():
            secret = User.objects.make_random_password(length=SECRET_SIZE)

        self.key = key
        self.secret = secret
        self.save()
        
admin.site.register(Token)