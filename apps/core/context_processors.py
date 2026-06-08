from apps.cart.models import Cart

def cart_count(request):
    """Add cart count to all templates"""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.get_total_items()
        except Cart.DoesNotExist:
            count = 0
    else:
        count = 0
    return {'cart_count': count}

def site_settings(request):
    """Add site settings to all templates"""
    return {
        'site_name': 'Vendora',
        'site_description': 'Multi-Vendor E-Commerce Platform',
        'site_year': 2026,
    }

def currency_settings(request):
    """Add active currency and currency choices to all templates"""
    from apps.core.currency import get_active_currency, CURRENCY_SYMBOLS, CURRENCY_RATES
    active_curr = get_active_currency(request)
    
    return {
        'active_currency': active_curr,
        'active_currency_symbol': CURRENCY_SYMBOLS.get(active_curr, '$'),
        'active_currency_rate': CURRENCY_RATES.get(active_curr, 1.0),
        'currency_choices': [
            {'code': code, 'symbol': sym, 'rate': CURRENCY_RATES[code]}
            for code, sym in CURRENCY_SYMBOLS.items()
        ]
    }