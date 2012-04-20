import inspect, handler

from piston.handler import typemapper

from django.core.urlresolvers import get_resolver, get_callable, get_script_prefix
from django.shortcuts import render_to_response
from django.template import RequestContext

def generate_doc(handler_cls):
    """
    Returns a `HandlerDocumentation` object
    for the given handler. Use this to generate
    documentation for your API.
    """
    if not type(handler_cls) is handler.HandlerMetaClass:
        raise ValueError("Give me handler, not %s" % type(handler_cls))
        
    return HandlerDocumentation(handler_cls)
    
class HandlerMethod(object):
    def __init__(self, method, stale=False):
        self.method = method
        self.stale = stale
        
    def iter_args(self):
        args, _, _, defaults = inspect.getargspec(self.method)

        for idx, arg in enumerate(args):
            if arg in ('self', 'request', 'form'):
                continue

            didx = len(args)-idx

            if defaults and len(defaults) >= didx:
                yield (arg, str(defaults[-didx]))
            else:
                yield (arg, None)
        
    def get_signature(self, parse_optional=True):
        spec = ""

        for argn, argdef in self.iter_args():
            spec += argn
            
            if argdef:
                spec += '=%s' % argdef
            
            spec += ', '
            
        spec = spec.rstrip(", ")
        
        if parse_optional:
            return spec.replace("=None", "=<optional>")
            
        return spec

    signature = property(get_signature)
        
    def get_doc(self):
        return inspect.getdoc(self.method)
    
    doc = property(get_doc)
    
    def get_name(self):
        return self.method.__name__
        
    name = property(get_name)
    
    def __repr__(self):
        return "<Method: %s>" % self.name
    
class HandlerDocumentation(object):
    def __init__(self, handler):
        self.handler = handler
        
    def get_methods(self, include_default=False):
        for method in "read create update delete".split():
            met = getattr(self.handler, method)
            stale = inspect.getmodule(met) is handler

            if not self.handler.is_anonymous:
                if met and (not stale or include_default):
                    yield HandlerMethod(met, stale)
            else:
                if not stale or met.__name__ == "read" \
                    and 'GET' in self.allowed_methods:
                    
                    yield HandlerMethod(met, stale)
        
    def get_all_methods(self):
        return self.get_methods(include_default=True)
        
    @property
    def is_anonymous(self):
        return handler.is_anonymous

    def get_model(self):
        return getattr(self, 'model', None)
            
    def get_doc(self):
        return self.handler.__doc__
    
    doc = property(get_doc)

    @property
    def name(self):
        return self.handler.__name__
    
    @property
    def allowed_methods(self):
        return self.handler.allowed_methods
    
    def get_resource_uri_template(self):
        """
        URI template processor.
        
        See http://bitworking.org/projects/URI-Templates/
        """
        def _convert(template, params=[]):
            """URI template converter"""
            paths = template % dict([p, "{%s}" % p] for p in params)
            return u'%s%s' % (get_script_prefix(), paths)
        
        try:
            resource_uri = self.handler.resource_uri()
            
            components = [None, [], {}]

            for i, value in enumerate(resource_uri):
                components[i] = value
        
            lookup_view, args, kwargs = components
            lookup_view = get_callable(lookup_view, True)

            possibilities = get_resolver(None).reverse_dict.getlist(lookup_view)
            
            for possibility, pattern in possibilities:
                for result, params in possibility:
                    if args:
                        if len(args) != len(params):
                            continue
                        return _convert(result, params)
                    else:
                        if set(kwargs.keys()) != set(params):
                            continue
                        return _convert(result, params)
        except:
            return None
        
    resource_uri_template = property(get_resource_uri_template)
    
    def __repr__(self):
        return u'<Documentation for "%s">' % self.name

def documentation_view(request):
    """
    Generic documentation view. Generates documentation
    from the handlers you've defined.
    """
    docs = [ ]

    for handler, (model, anonymous) in typemapper.iteritems():
        docs.append(generate_doc(handler))
        
    return render_to_response('documentation.html', 
        { 'docs': docs }, RequestContext(request))
