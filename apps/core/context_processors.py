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