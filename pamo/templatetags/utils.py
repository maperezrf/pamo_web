from django import template
import numpy as np

register = template.Library()

@register.filter
def replace_spaces(value):
    return value.replace(' ', '~')

@register.filter
def format_number(value):
    if (value == 'nan') | (value == ''):
        return '$0'
    else: 
        return "${:,.0f}".format(float(value))

@register.filter
def format_percent(value):
    return "{:,.0f}%".format(int(float(value)*100))    