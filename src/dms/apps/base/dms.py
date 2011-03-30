import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from adlibre.converter import FileConverter

from base.models import (Rule, available_validators, available_doccodes,
    available_storages, available_securities)
from base.utils import ValidatorProvider, StorageProvider, SecurityProvider, DocCodeProvider


# for codes to throw http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

class DmsException(Exception):

    def __init__(self, value, code):
        self.parameter = value
        self.code = code

    def __str__(self):
        return (repr(self.parameter), self.code)


class DmsBase():

    def get_plugins(self):
        plugins = []
        for plugin in available_doccodes():
            plugins.append(plugin)
        for plugin in available_validators():
            plugins.append(plugin)
        for plugin in available_securities():
            plugins.append(plugin)
            # TODO: Add available storages
        return plugins

    def get_rules(self):
        return Rule.objects.all()


class DmsRule():
    """
    DmsRule object
    """

    def __init__(self, id_rule):

        self.id_rule = id_rule

        try:
            self.rule = Rule.objects.get(id=id_rule)
        except ObjectDoesNotExist:
            raise DmsException("No rule found for id " + id_rule, 404)

        self.hashplugin = self.rule.get_security('Hash')
        self.storage = self.rule.get_storage()
        self.security = self.rule.get_securities()

    
    def get_setting(self):
        pass

    
    def set_setting(self):
        pass


    def get_file_list(self):
        return self.rule.get_storage().get_list(self.id_rule)


    def get_rule_details(self):
        # FIXME: I don't like how this is written, but it will do for now
        rule = self.rule
        rule.doccode = self.rule.get_doccode().name
        rule.storage = self.rule.get_storage().name
        securities = self.rule.get_securities()
        rule.securities = ",".join([security.name for security in securities])
        validators = self.rule.get_validators()
        rule.validators = ",".join([validator.name for validator in validators])

        return rule

class DmsDocument():
    """
    Our individual document, or object in the Dms
    """
    def __init__(self, document, revision=1):

        self.document = document
        self.revision = revision

        try:
            self.rule = Rule.objects.match(document)
        except ObjectDoesNotExist:
            raise DmsException("No rule found for file " + document, 404)

        self.hashplugin = self.rule.get_security('Hash')
        self.storage = self.rule.get_storage()
        self.security = self.rule.get_securities()


    def check_request(self, request, is_retrieval=True):
        # check against all validator
        for validator in self.rule.get_validators():
            if validator.is_retrieval_action and validator.active and is_retrieval:
                try:
                    validator.perform(request, self.document)
                except:
                    raise
            elif validator.is_storing_action and validator.active and not is_retrieval:
                try:
                    validator.perform(request, self.document)
                except:
                    raise


    def check_security(self, request, is_retrieval=True):
        # check against all securities
        for security in self.rule.get_securities():
            if security.is_retrieval_action and security.active and is_retrieval:
                try:
                    return security.perform(request, self.document)
                except:
                    raise
            elif security.is_storing_action and security.active and not is_retrieval:
                try:
                    security.perform(request, self.document)
                except:
                    raise


    def check_hash(self, hashcode):
        # check hashcode
        if self.hashplugin and self.hashplugin.active and hashcode==None:
            raise DmsException('Hash Required', 403)
        elif self.hashplugin and self.hashplugin.active :
            # TODO: Make salt / secret key a plugin option
            if self.hashplugin.perform(self.document, settings.SECRET_KEY) != hashcode:
                raise DmsException('Invalid hashcode', 403)
        else:
            pass


    def get_file(self, request, hashcode=None, request_extension=None):

        # FIXME: Do these raise an exception on failure, or return False?
        self.check_security(request, True)
        self.check_request(request, True)
        self.check_hash(hashcode) # FIXME: should hashplugin be validated as part of the validate request phase???

        try:
            filepath = self.storage.get(self.document, self.revision)
        except:
            raise DmsException('No file or revision match', 404)

        # Convert the file if necessary
        new_file = FileConverter(filepath, request_extension)
        try:
            mimetype, content = new_file.convert()
        except TypeError:
            raise DmsException('Unable to convert to requested format', 405)

        if request_extension:
            filename = "%s.%s" % (self.document, request_extension)
        else:
            filename = os.path.basename(filepath)
            rev_document, rev_extension = os.path.splitext(filename)
            filename = "%s%s" % (rev_document, rev_extension)

        return (content, filename, mimetype)


    def get_meta_data(self, request):

        self.check_security(request, True)
        self.check_request(request, True)

        return self.storage.get_meta_data(self.document) # FIXME, we shouldn't need to pass document to storage


    def get_hash(self):

        if self.hashplugin and self.hashplugin.active:
            return self.hashplugin.perform(self.document, settings.SECRET_KEY) # FIXME, we shouldn't need to pass document to hash plugin
        else:
            return None


    def set_file(self, request, file_content, new_revision=True, append_content=False):
        """
        Upload file
        """
        # new_revision = False = overwrite if exists,
        # new_revision = True = make backup revision

        self.check_security(request, False)
        self.check_request(request, False)

        return self.storage.store(file_content)


    def delete_file(self):

        # TODO: Add security checks here.

        return self.storage.delete(self.document, self.revision)


    def set_meta_data(self):
        pass
