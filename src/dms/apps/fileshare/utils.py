class DocCodePluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls
        cls.plugin_type = "Document Code"


class DocCodeProvider:
    __metaclass__ = DocCodePluginMount


class ValidatorPluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls
        cls.plugin_type = "Validation"


class ValidatorProvider:
    __metaclass__ = ValidatorPluginMount



class StoragePluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls
        cls.plugin_type = "Storage"


class StorageProvider:
    __metaclass__ = StoragePluginMount


class SecurityPluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls
        cls.plugin_type = "Security"


class SecurityProvider:
    __metaclass__ = SecurityPluginMount

