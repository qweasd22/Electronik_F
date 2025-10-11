from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножение значения на аргумент."""
    try:
        return value * arg
    except (TypeError, ValueError):
        return value
