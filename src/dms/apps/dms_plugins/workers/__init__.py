class Plugin(object):
    title = 'Plugin'
    description = 'Generic plugin class for inheritance'
    active = False
    plugin_type = None

    def __init__(self):
        self.index = getattr(self, 'index', 0)

    def get_plugin_type(self):
        return getattr(self, 'plugin_type', None)

class PluginError(Exception):
    pass

class PluginWarning(Exception):
    pass

class BreakPluginChain(Exception):
    pass