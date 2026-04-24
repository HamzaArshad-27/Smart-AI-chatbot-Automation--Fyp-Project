# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Cart, CartItem
from .models import Product

@login_required
def cart_view(request):
    """Display shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'cart/view.html', context)

# cart/views.py


@login_required
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check stock availability
    if quantity > product.stock_quantity:
        error_msg = f'Sorry, only {product.stock_quantity} items available.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect(request.POST.get('next', 'products:detail', product.slug))
    
    # Get or create cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Check if adding more would exceed stock
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock_quantity:
            error_msg = f'Sorry, only {product.stock_quantity} items available in stock.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            success_msg = f'{product.name} quantity updated in cart!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'cart_count': cart.get_total_items()
                })
            messages.success(request, success_msg)
    else:
        success_msg = f'{product.name} added to cart!'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': success_msg,
                'cart_count': cart.get_total_items()
            })
        messages.success(request, success_msg)
    
    # Check if there's a next parameter (redirect after add)
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    
    # Default: redirect back to product detail
    return redirect('products:detail', slug=product.slug)
@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate quantity
        if quantity < 1:
            cart_item.delete()
            messages.success(request, 'Item removed from cart.')
        elif quantity > cart_item.product.stock_quantity:
            messages.error(request, f'Sorry, only {cart_item.product.stock_quantity} items available.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully.')
        
        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_total': cart_item.cart.get_total(),
                'item_count': cart_item.cart.get_total_items(),
                'item_subtotal': cart_item.get_subtotal()
            })
        
        return redirect('cart:view')

@login_required
def remove_cart_item(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart.')
        
        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = Cart.objects.get(user=request.user)
            return JsonResponse({
                'success': True,
                'cart_total': cart.get_total(),
                'item_count': cart.get_total_items()
            })
        
        return redirect('cart:view')

@login_required
def clear_cart(request):
    """Clear all items from cart"""
    if request.method == 'POST' or request.method == 'GET':
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart.items.all().delete()
            messages.success(request, 'Cart cleared successfully.')
        return redirect('cart:view')