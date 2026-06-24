CURRENCY_RATES = {
    'USD': 1.0,
    'PKR': 278.0,
    'SAR': 3.75,
    'AED': 3.67,
    'EUR': 0.92,
    'GBP': 0.79,
}

CURRENCY_SYMBOLS = {
    'USD': '$',
    'PKR': 'Rs.',
    'SAR': 'SR',
    'AED': 'AED',
    'EUR': '€',
    'GBP': '£',
}

def get_active_currency(request):
    """
    Get active currency from session.
    If not set, default to USD.
    """
    if not request or not hasattr(request, 'session'):
        return 'USD'
    return request.session.get('currency', 'USD')

def convert_currency(amount, to_currency, from_currency='USD'):
    """
    Converts amount from from_currency to to_currency.
    """
    if amount is None:
        return 0.0
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return 0.0
    
    # Get rates relative to USD
    from_rate = CURRENCY_RATES.get(from_currency, 1.0)
    to_rate = CURRENCY_RATES.get(to_currency, 1.0)
    
    # Convert to USD base first, then convert to target
    usd_amount = amount / from_rate
    converted_amount = usd_amount * to_rate
    
    return converted_amount

def format_currency(amount, currency_code):
    """
    Formats the amount with the correct symbol.
    """
    symbol = CURRENCY_SYMBOLS.get(currency_code, '$')
    if amount is None:
        amount = 0.0
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        amount = 0.0
        
    return f"{symbol} {amount:,.2f}"
