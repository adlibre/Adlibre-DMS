from plugins import PluginMount

#WORKFLOW: Request -> Security -> Action Process -> Response
#ACTIONS: Store, Retrieve

#settings_field_name is the name of the collection of these plugins in base.models.DoccodePluginSettings

class BeforeStoragePluginPoint(object):
    __metaclass__ = PluginMount
    settings_field_name = 'before_storage_plugins'
    
class BeforeRetrievalPluginPoint(object):
    __metaclass__ = PluginMount
    settings_field_name = 'before_retrieval_plugins'
