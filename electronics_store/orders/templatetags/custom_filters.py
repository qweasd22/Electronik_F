# orders/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (TypeError, ValueError):
        return None
from django import template

register = template.Library()

@register.filter(name='Seller')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножение значения на аргумент."""
    try:
        return value * arg
    except (TypeError, ValueError):
        return value
