from django import template
from apps.core.currency import get_active_currency, convert_currency, format_currency, CURRENCY_SYMBOLS

register = template.Library()

@register.filter
def currency_format(value, request):
    """
    Format a decimal/float price value based on user's active session currency.
    Usage: {{ product.price|currency_format:request }}
    """
    if value is None:
        value = 0.0
    active_curr = get_active_currency(request)
    # Database prices are stored in USD (base), convert to active visitor currency
    converted = convert_currency(value, active_curr, 'USD')
    return format_currency(converted, active_curr)

@register.filter
def currency_convert(value, request):
    """
    Convert a decimal/float price value to user's active session currency (numeric only).
    Usage: {{ product.price|currency_convert:request }}
    """
    if value is None:
        return 0.0
    active_curr = get_active_currency(request)
    return round(convert_currency(value, active_curr, 'USD'), 2)

@register.simple_tag
def currency_symbol(request):
    """
    Get the currency symbol for active session.
    Usage: {% currency_symbol request %}
    """
    active_curr = get_active_currency(request)
    return CURRENCY_SYMBOLS.get(active_curr, '$')

@register.simple_tag
def currency_code(request):
    """
    Get the currency code for active session.
    Usage: {% currency_code request %}
    """
    return get_active_currency(request)

@register.filter
def order_currency_format(value, order_or_currency):
    """
    Format a price value based on an order's currency.
    Usage: {{ order_item.price|order_currency_format:order }}
    or: {{ order.total_amount|order_currency_format:order.currency }}
    """
    if value is None:
        value = 0.0
    
    # Get currency string
    if hasattr(order_or_currency, 'currency'):
        currency = order_or_currency.currency
    else:
        currency = str(order_or_currency)
        
    if not currency:
        currency = 'USD'
        
    converted = convert_currency(value, currency, 'USD')
    return format_currency(converted, currency)


@register.filter
def replace_underscore(value, arg=" "):
    """
    Replace underscores with space or another string.
    Usage: {{ value|replace_underscore:" " }}
    """
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return value.replace('_', arg)


