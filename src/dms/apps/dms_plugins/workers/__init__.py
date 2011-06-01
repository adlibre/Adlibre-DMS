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

class DmsException(Exception):
    def __init__(self, value, code):
        self.parameter = value
        self.code = code

    def __str__(self):
        return (repr(self.parameter), self.code)

