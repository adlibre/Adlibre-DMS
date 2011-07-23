from plugins import PluginMount

#settings_field_name is the name of the collection of these plugins in base.models.DoccodePluginSettings

class BeforeStoragePluginPoint(object):
    __metaclass__ = PluginMount
    settings_field_name = 'before_storage_plugins'

class BeforeRetrievalPluginPoint(object):
    __metaclass__ = PluginMount
    settings_field_name = 'before_retrieval_plugins'

class BeforeRemovalPluginPoint(object):
    __metaclass__ = PluginMount
    settings_field_name = 'before_removal_plugins'

class BeforeUpdatePluginPoint(object):
    __metaclass__ = PluginMount
    settings_field_name = 'before_update_plugins'