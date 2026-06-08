from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q, Avg, Sum
from apps.products.models import Product, Category
import json

def home(request):
    """Home page with all product sections"""
    
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )[:10]
    
    featured_products = Product.objects.filter(is_active=True, is_featured=True).prefetch_related('images')[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'core/home.html', context)

def products_api(request):
    """API endpoint for product loading"""
    category = request.GET.get('category', '')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', '')
    tab = request.GET.get('tab', 'featured')  # featured, new, reviewed, selling, rated
    
    products = Product.objects.filter(is_active=True).select_related('category', 'company').prefetch_related('images', 'reviews')
    
    # Apply filters
    if category:
        products = products.filter(category__slug=category)
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    # Apply tab sorting
    if tab == 'new':
        products = products.order_by('-created_at')
    elif tab == 'reviewed':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif tab == 'selling':
        products = products.annotate(total_sold_count=Sum('order_items__quantity')).order_by('-total_sold_count')
    elif tab == 'rated':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:  # featured
        products = products.filter(is_featured=True)
    
    products = products[:12]
    
    products_data = []
    for product in products:
        # Get first image
        images = list(product.images.all())
        first_image = images[0] if images else None
        image_url = first_image.image.url if first_image else None
        
        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'compare_price': float(product.compare_price) if product.compare_price else None,
            'discount_percentage': product.discount_percentage,
            'average_rating': float(product.average_rating) if product.average_rating else 0,
            'total_reviews': product.total_reviews,
            'image': image_url,
            'category': product.category.name if product.category else '',
            'sku': product.sku,
        })
    
    return JsonResponse({
        'products': products_data,
        'count': len(products_data),
    })


def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

def faq(request):
    return render(request, 'core/faq.html')

def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def set_currency(request):
    """Set active currency in user session"""
    from django.shortcuts import redirect
    currency = request.GET.get('currency', 'USD')
    from apps.core.currency import CURRENCY_RATES
    if currency in CURRENCY_RATES:
        request.session['currency'] = currency
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('core:home')