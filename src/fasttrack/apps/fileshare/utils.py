class ValidatorPluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls


class ValidatorProvider:
    __metaclass__ = ValidatorPluginMount



class SplitterPluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls


class SplitterProvider:
    __metaclass__ = SplitterPluginMount



class StoragePluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls


class StorageProvider:
    __metaclass__ = StoragePluginMount


class HashPluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.name] = cls


class HashProvider:
    __metaclass__ = HashPluginMount

