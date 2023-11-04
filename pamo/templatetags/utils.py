from django import template

register = template.Library()

@register.filter
def replace_spaces(value):
    return value.replace(' ', '~')