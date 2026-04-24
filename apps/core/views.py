from django.shortcuts import render
from django.http import HttpResponse
from apps.products.models import Product, Category
from django.db.models import Count, Q

def home(request):
    """Home page view"""
    # Get featured products (products with is_featured=True)
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category', 'company')[:8]
    
    # Get latest products
    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'company').order_by('-created_at')[:8]
    
    # Get categories with product count
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )[:8]
    
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    }
    
    return render(request, 'core/home.html', context)

def about(request):
    """About page view"""
    return render(request, 'core/about.html')

def contact(request):
    """Contact page view"""
    return render(request, 'core/contact.html')

def faq(request):
    """FAQ page view"""
    return render(request, 'core/faq.html')

def terms(request):
    """Terms and conditions page view"""
    return render(request, 'core/terms.html')

def privacy(request):
    """Privacy policy page view"""
    return render(request, 'core/privacy.html')