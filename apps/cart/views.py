from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Cart, CartItem
from apps.products.models import Product

@login_required
def cart_view(request):
    """Display shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {'cart': cart}
    return render(request, 'cart/view.html', context)

@login_required
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if product.stock_quantity <= 0:
        messages.error(request, 'Product is out of stock!')
        return redirect('products:detail', slug=product.slug)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity + 1 <= product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Added another {product.name} to cart!')
        else:
            messages.error(request, f'Only {product.stock_quantity} items available!')
    else:
        messages.success(request, f'{product.name} added to cart!')
    
    return redirect('cart:view')

@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
        elif quantity <= cart_item.product.stock_quantity:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully!')
        else:
            messages.error(request, f'Only {cart_item.product.stock_quantity} items available!')
    
    return redirect('cart:view')

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'{product_name} removed from cart!')
    return redirect('cart:view')

@login_required
def clear_cart(request):
    """Clear entire cart"""
    cart = Cart.objects.get(user=request.user)
    cart.clear()
    messages.success(request, 'Cart cleared successfully!')
    return redirect('cart:view')