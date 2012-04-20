from django.db import models
from django.contrib.auth.models import User

KEY_SIZE = 16
SECRET_SIZE = 16

class ConsumerManager(models.Manager):
    def create_consumer(self, name, description=None, user=None):
        """
        Shortcut to create a consumer with random key/secret.
        """
        consumer, created = self.get_or_create(name=name)

        if user:
            consumer.user = user

        if description:
            consumer.description = description

        if created:
            consumer.generate_random_codes()

        return consumer
    
    _default_consumer = None

class ResourceManager(models.Manager):
    _default_resource = None

    def get_default_resource(self, name):
        """
        Add cache if you use a default resource.
        """
        if not self._default_resource:
            self._default_resource = self.get(name=name)

        return self._default_resource        

class TokenManager(models.Manager):
    def create_token(self, consumer, token_type, timestamp, user=None):
        """
        Shortcut to create a token with random key/secret.
        """
        token, created = self.get_or_create(consumer=consumer, 
                                            token_type=token_type, 
                                            timestamp=timestamp,
                                            user=user)

        if created:
            token.generate_random_codes()

        return token