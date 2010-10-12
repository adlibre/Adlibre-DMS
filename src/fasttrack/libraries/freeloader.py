from django.template import TemplateDoesNotExist

def load_template_source(template_name, template_dirs=None):
    try:
        return open(template_name).read(), template_name
    except IOError:
        raise TemplateDoesNotExist, template_name
load_template_source.is_usable = True

