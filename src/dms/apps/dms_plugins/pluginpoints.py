from plugins import PluginMount

#WORKFLOW: Request -> Security -> Action Process -> Response
#ACTIONS: Store, Retrieve

class BeforeStoragePluginPoint(object):
    __metaclass__ = PluginMount
    pass
    
class BeforeRetrievalPluginPoint(object):
    __metaclass__ = PluginMount
    pass
