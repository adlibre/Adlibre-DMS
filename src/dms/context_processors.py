from django.conf import settings

def theme_template_base(context):
    return {'THEME_TEMPLATE': settings.THEME_NAME+'_theme_base.html'}

def theme_name(context):
    return {'THEME_NAME': settings.THEME_NAME}

def demo(context):
    """ Returns Demo Mode Boolean Context Variable """
    return {'DEMO': settings.DEMO}

