from django.apps import AppConfig
from orders.templatetags import custom_filters

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

from django import template

register = template.Library

register.filter('custom_filter', custom_filters)