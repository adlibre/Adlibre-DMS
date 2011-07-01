from plugins.models import Plugin as DjangoPlugin, ENABLED
from plugins.utils import get_plugin_name

from dms_plugins.models import PluginOption

class Plugin(object):
    title = 'Plugin'
    description = 'Generic plugin class for inheritance'
    plugin_type = None
    configurable_fields = []

    def __init__(self):
        self.index = getattr(self, 'index', 0)

    def get_plugin_type(self):
        return getattr(self, 'plugin_type', None)

    def get_form(self):
        return getattr(self, 'form', None)

    def get_model(self):
        return DjangoPlugin.objects.get(name = get_plugin_name(self.__class__))

    def get_configuration_form(self, mapping, *form_args, **form_kwargs):
        config_form = None
        if self.get_form():
            plugin_model = self.get_model()
            plugin_options = PluginOption.objects.filter(plugin = plugin_model, pluginmapping = mapping)
            if plugin_options.count != len(self.configurable_fields):
                new_plugin_options = []
                for field in self.configurable_fields:
                    if not plugin_options.filter(name = field).count():
                        new_plugin_options.append(
                            PluginOption(   plugin = plugin_model,
                                        pluginmapping = mapping,
                                        name = field,
                                        value = getattr(self, field, None)
                                        ))
                plugin_options = list(plugin_options) + new_plugin_options
            form_class = self.get_form()
            if not form_kwargs.get('initial', None):
                initial = dict([(x.name, x.value) for x in plugin_options])
                form_kwargs['initial'] = initial
            config_form = form_class(options = plugin_options, *form_args, **form_kwargs)
        return config_form

    def is_active(self):
        return self.get_model().status == ENABLED

    active = property(is_active)

    def render(self):
        return self.title + ": " + self.description

    def get_option(self, option, doccode):
        value = getattr(self, option, None)
        try:
            plugin_options = PluginOption.objects.filter(
                                plugin = self.get_model(), 
                                pluginmapping__doccode = doccode.get_id(),
                                name = option
                                )
        except PluginOption.DoesNotExist:
            pass
        return value

class DmsException(Exception):
    def __init__(self, value, code):
        self.parameter = value
        self.code = code

    def __str__(self):
        return super(DmsException, self).__str__() + (" %s - %s" % (self.code, repr(self.parameter)))

    def __repr__(self):
        return super(DmsException, self).__repr__() + (" %s - %s" % (self.code, repr(self.parameter)))

    def __unicode__(self):
        return unicode(str(self))

class PluginError(DmsException):
    pass

class PluginWarning(Exception):
    pass

class BreakPluginChain(Exception):
    pass



