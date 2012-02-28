
from django import template
register = template.Library()

@register.tag(name="get_key_li_item")
def do_key_li_item(parser, token):
    try:
        # splitings args provided
        tag_name, keys_dict, key_item = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly two arguments" % token.contents.split()[0])
    return ProvideLiElement(keys_dict, key_item)

class ProvideLiElement(template.Node):
    def __init__(self, keys_dict, key_item):
        self.keys_dict = template.Variable(keys_dict)
        self.key_item = template.Variable(key_item)

    def render(self, context):
        try:
            item = self.key_item.resolve(context)
            dict = self.keys_dict.resolve(context)
            value = dict[item]
            if item == u'date':
                item = u'Creation Date'
            if item == u'description':
                item = u'Description'
            resp_string = unicode(item)+u': '+unicode(value)
            return resp_string
        except template.VariableDoesNotExist:
            return ''

