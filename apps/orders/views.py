from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from .models import Order, OrderItem
from apps.cart.models import Cart
import uuid
import csv
import json

@login_required
def checkout(request):
    """Checkout page"""
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    if cart.get_total_items() == 0:
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart:view')
    
    context = {
        'cart': cart,
        'total': cart.get_total(),
    }
    
    return render(request, 'orders/checkout.html', context)

@login_required
@transaction.atomic
def create_order(request):
    """Create order from cart"""
    if request.method != 'POST':
        return redirect('cart:view')
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart:view')
    
    if cart.get_total_items() == 0:
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart:view')
    
    # Create order
    order_number = str(uuid.uuid4()).replace('-', '')[:12].upper()
    
    # Get the first product's company (for multi-vendor, you might need to split orders)
    first_item = cart.items.first()
    company = first_item.product.company if first_item else None
    
    subtotal = cart.get_total()
    try:
        shipping_cost = float(request.POST.get('shipping_cost', 0) or 0)
    except (ValueError, TypeError):
        shipping_cost = 0.0
    try:
        tax_amount = float(request.POST.get('tax_amount', 0) or 0)
    except (ValueError, TypeError):
        tax_amount = 0.0
    try:
        discount_amount = float(request.POST.get('discount_amount', 0) or 0)
    except (ValueError, TypeError):
        discount_amount = 0.0

    total_amount = float(subtotal) + shipping_cost + tax_amount - discount_amount

    order = Order.objects.create(
        user=request.user,
        company=company,
        order_number=order_number,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        shipping_address=request.POST.get('shipping_address'),
        shipping_city=request.POST.get('shipping_city'),
        shipping_state=request.POST.get('shipping_state'),
        shipping_country=request.POST.get('shipping_country'),
        shipping_postal_code=request.POST.get('shipping_postal_code'),
        shipping_phone=request.POST.get('shipping_phone'),
        payment_method=request.POST.get('payment_method', 'cod'),
        notes=request.POST.get('notes', '')
    )
    
    # Create order items and update stock
    for cart_item in cart.items.all():
        # Check stock availability
        if cart_item.quantity > cart_item.product.stock_quantity:
            messages.error(request, f'Insufficient stock for {cart_item.product.name}')
            return redirect('cart:view')
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            seller=cart_item.product.seller,
            quantity=cart_item.quantity,
            price=cart_item.product.price
        )
        
        # Update stock
        cart_item.product.update_stock(cart_item.quantity)
    
    # Clear cart
    cart.clear()
    
    messages.success(request, f'Order #{order_number} created successfully!')
    return redirect('orders:success', order_id=order.id)

@login_required
def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})

@login_required
def order_detail(request, order_id):
    """Order details page"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to view this order
    if request.user.role == 'company':
        if order.company != request.user.company_profile:
            messages.error(request, 'You do not have permission to view this order')
            return redirect('dashboard:index')
    elif request.user.role == 'seller':
        # Check if seller is associated with any item in the order
        seller_items = order.items.filter(seller=request.user.seller_profile)
        if not seller_items.exists():
            messages.error(request, 'You do not have permission to view this order')
            return redirect('dashboard:index')
    elif request.user.role == 'customer':
        if order.user != request.user:
            messages.error(request, 'You do not have permission to view this order')
            return redirect('dashboard:index')
    
    return render(request, 'orders/detail.html', {'order': order})

@login_required
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['pending', 'approved']:
        order.status = 'cancelled'
        order.save()
        
        # Restore stock
        for item in order.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.total_sold -= item.quantity
            product.save()
        
        messages.success(request, 'Order cancelled successfully!')
    else:
        messages.error(request, 'Order cannot be cancelled at this stage!')
    
    return redirect('orders:detail', order_id=order.id)

@login_required
def track_order(request, order_id):
    """Track order status"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/track.html', {'order': order})

# Company Order Management Views
@login_required
@user_passes_test(lambda u: u.role == 'company')
def company_orders(request):
    """View all orders for a company"""
    company = request.user.company_profile
    orders = Order.objects.filter(company=company).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'total_orders': paginator.count,
        'pending_count': Order.objects.filter(company=company, status='pending').count(),
        'approved_count': Order.objects.filter(company=company, status='approved').count(),
        'processing_count': Order.objects.filter(company=company, status='processing').count(),
        'shipped_count': Order.objects.filter(company=company, status='shipped').count(),
        'delivered_count': Order.objects.filter(company=company, status='delivered').count(),
    }
    return render(request, 'orders/company_orders.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'company')
def approve_order(request, order_id):
    """Approve an order"""
    order = get_object_or_404(Order, id=order_id, company=request.user.company_profile)
    
    if order.status == 'pending':
        order.status = 'approved'
        order.approved_at = timezone.now()
        order.save()
        messages.success(request, f'Order #{order.order_number} has been approved!')
    else:
        messages.error(request, 'This order cannot be approved at this stage.')
    
    return redirect('orders:company_orders')

@login_required
@user_passes_test(lambda u: u.role == 'company')
def process_order(request, order_id):
    """Mark order as processing"""
    order = get_object_or_404(Order, id=order_id, company=request.user.company_profile)
    
    if order.status == 'approved':
        order.status = 'processing'
        order.save()
        messages.success(request, f'Order #{order.order_number} is now being processed!')
    else:
        messages.error(request, 'This order cannot be processed at this stage.')
    
    return redirect('orders:company_orders')

@login_required
@user_passes_test(lambda u: u.role == 'company')
def ship_order(request, order_id):
    """Mark order as shipped"""
    order = get_object_or_404(Order, id=order_id, company=request.user.company_profile)
    
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number', '')
        
        if order.status == 'processing':
            order.status = 'shipped'
            order.shipped_at = timezone.now()
            order.tracking_number = tracking_number
            order.save()
            messages.success(request, f'Order #{order.order_number} has been shipped!')
        else:
            messages.error(request, 'This order cannot be shipped at this stage.')
        
        return redirect('orders:company_orders')
    
    return render(request, 'orders/ship_order.html', {'order': order})

# Seller Order Management Views
@login_required
@user_passes_test(lambda u: u.role == 'seller')
def seller_orders(request):
    """View all orders assigned to a seller"""
    seller = request.user.seller_profile
    order_items = OrderItem.objects.filter(seller=seller).select_related('order', 'product').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        order_items = order_items.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(order_items, 20)
    page = request.GET.get('page')
    order_items = paginator.get_page(page)
    
    context = {
        'order_items': order_items,
        'status_filter': status_filter,
        'total_items': order_items.paginator.count,
        'pending_count': OrderItem.objects.filter(seller=seller, status='pending').count(),
        'processing_count': OrderItem.objects.filter(seller=seller, status='processing').count(),
        'shipped_count': OrderItem.objects.filter(seller=seller, status='shipped').count(),
        'delivered_count': OrderItem.objects.filter(seller=seller, status='delivered').count(),
    }
    return render(request, 'orders/seller_orders.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'seller')
def process_order_item(request, item_id):
    """Process an order item"""
    order_item = get_object_or_404(OrderItem, id=item_id, seller=request.user.seller_profile)
    
    if order_item.status == 'pending':
        order_item.status = 'processing'
        order_item.save()
        
        # Update main order status if all items are processing
        order = order_item.order
        if all(item.status in ['processing', 'shipped', 'delivered'] for item in order.items.all()):
            if order.status == 'approved':
                order.status = 'processing'
                order.save()
        
        messages.success(request, f'Order item for {order_item.product.name} is now being processed!')
    else:
        messages.error(request, 'This order item cannot be processed at this stage.')
    
    return redirect('orders:seller_orders')

@login_required
@user_passes_test(lambda u: u.role == 'seller')
def ship_order_item(request, item_id):
    """Mark order item as shipped"""
    order_item = get_object_or_404(OrderItem, id=item_id, seller=request.user.seller_profile)
    
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number', '')
        
        if order_item.status == 'processing':
            order_item.status = 'shipped'
            order_item.tracking_number = tracking_number
            order_item.save()
            
            # Update main order status if all items are shipped
            order = order_item.order
            if all(item.status in ['shipped', 'delivered'] for item in order.items.all()):
                order.status = 'shipped'
                order.shipped_at = timezone.now()
                order.tracking_number = tracking_number
                order.save()
            
            messages.success(request, f'Order item for {order_item.product.name} has been shipped!')
        else:
            messages.error(request, 'This order item cannot be shipped at this stage.')
        
        return redirect('orders:seller_orders')
    
    return render(request, 'orders/ship_item.html', {'order_item': order_item})

@login_required
@user_passes_test(lambda u: u.role == 'seller')
def deliver_order_item(request, item_id):
    """Mark order item as delivered"""
    order_item = get_object_or_404(OrderItem, id=item_id, seller=request.user.seller_profile)
    
    if order_item.status == 'shipped':
        order_item.status = 'delivered'
        order_item.save()
        
        # Update main order status if all items are delivered
        order = order_item.order
        if all(item.status == 'delivered' for item in order.items.all()):
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.save()
        
        messages.success(request, f'Order item for {order_item.product.name} has been delivered!')
    else:
        messages.error(request, 'This order item cannot be marked as delivered at this stage.')
    
    return redirect('orders:seller_orders')

@login_required
@user_passes_test(lambda u: u.role == 'company')
def deliver_order(request, order_id):
    """Mark order as delivered"""
    order = get_object_or_404(Order, id=order_id, company=request.user.company_profile)
    
    if order.status == 'shipped':
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        if order.payment_method == 'cod':
            order.payment_status = 'paid'
        order.save()
        
        # Also mark all order items as delivered
        for item in order.items.all():
            if item.status != 'delivered':
                item.status = 'delivered'
                item.save()
        
        messages.success(request, f'Order #{order.order_number} has been marked as delivered!')
    else:
        messages.error(request, 'This order cannot be marked as delivered at this stage.')
    
    return redirect('orders:company_orders')

@login_required
@user_passes_test(lambda u: u.role == 'company')
def order_detail_api(request, order_id):
    """API returning order details for dynamic offcanvas drawer"""
    order = get_object_or_404(Order, id=order_id, company=request.user.company_profile)
    
    items = []
    for item in order.items.all():
        image_url = ""
        if item.product.images.first():
            image_url = item.product.images.first().image.url
        items.append({
            'name': item.product.name,
            'quantity': item.quantity,
            'price': str(item.price),
            'total': str(item.total),
            'image_url': image_url
        })
        
    data = {
        'id': order.id,
        'order_number': order.order_number,
        'created_at': order.created_at.strftime('%Y-%m-%d %I:%M %p'),
        'status': order.status,
        'status_display': order.get_status_display(),
        'payment_status': order.payment_status,
        'payment_status_display': order.get_payment_status_display(),
        'payment_method': order.payment_method,
        'payment_method_display': order.get_payment_method_display(),
        'subtotal': str(order.subtotal),
        'shipping_cost': str(order.shipping_cost),
        'tax_amount': str(order.tax_amount),
        'discount_amount': str(order.discount_amount),
        'total_amount': str(order.total_amount),
        'shipping_address': order.shipping_address,
        'shipping_city': order.shipping_city,
        'shipping_state': order.shipping_state,
        'shipping_country': order.shipping_country,
        'shipping_postal_code': order.shipping_postal_code,
        'shipping_phone': order.shipping_phone,
        'customer_name': order.user.get_full_name() or order.user.email,
        'customer_email': order.user.email,
        'notes': order.notes,
        'tracking_number': order.tracking_number,
        'items': items
    }
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.role == 'company')
def update_order_status_api(request, order_id):
    """API to transition order status instantly via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
        
    order = get_object_or_404(Order, id=order_id, company=request.user.company_profile)
    data = json.loads(request.body) if request.body else {}
    action = data.get('action')
    
    if action == 'approve':
        if order.status == 'pending':
            order.status = 'approved'
            order.approved_at = timezone.now()
            order.save()
            return JsonResponse({'success': True, 'new_status': order.status, 'status_display': order.get_status_display()})
            
    elif action == 'process':
        if order.status == 'approved':
            order.status = 'processing'
            order.save()
            return JsonResponse({'success': True, 'new_status': order.status, 'status_display': order.get_status_display()})
            
    elif action == 'ship':
        if order.status == 'processing':
            tracking_number = data.get('tracking_number', '')
            order.status = 'shipped'
            order.shipped_at = timezone.now()
            order.tracking_number = tracking_number
            order.save()
            return JsonResponse({'success': True, 'new_status': order.status, 'status_display': order.get_status_display(), 'tracking_number': tracking_number})
            
    elif action == 'deliver':
        if order.status == 'shipped':
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            if order.payment_method == 'cod':
                order.payment_status = 'paid'
            order.save()
            
            # Mark items delivered
            for item in order.items.all():
                item.status = 'delivered'
                item.save()
                
            return JsonResponse({
                'success': True, 
                'new_status': order.status, 
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_status_display': order.get_payment_status_display()
            })
            
    return JsonResponse({'error': f'Cannot update order status to action {action} from status {order.status}'}, status=400)

@login_required
@user_passes_test(lambda u: u.role == 'company')
@transaction.atomic
def bulk_approve_orders(request):
    """Bulk approve selected orders"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
        
    try:
        data = json.loads(request.body)
        order_ids = data.get('order_ids', [])
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
        
    company = request.user.company_profile
    orders = Order.objects.filter(id__in=order_ids, company=company, status='pending')
    count = 0
    for order in orders:
        order.status = 'approved'
        order.approved_at = timezone.now()
        order.save()
        count += 1
        
    return JsonResponse({'success': True, 'message': f'Successfully approved {count} order(s)'})

@login_required
@user_passes_test(lambda u: u.role == 'company')
@transaction.atomic
def bulk_cancel_orders(request):
    """Bulk cancel selected orders and restore product inventory"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
        
    try:
        data = json.loads(request.body)
        order_ids = data.get('order_ids', [])
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
        
    company = request.user.company_profile
    orders = Order.objects.filter(id__in=order_ids, company=company, status__in=['pending', 'approved'])
    count = 0
    for order in orders:
        order.status = 'cancelled'
        order.save()
        count += 1
        
        # Restore stock
        for item in order.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.total_sold -= item.quantity
            product.save()
            
    return JsonResponse({'success': True, 'message': f'Successfully cancelled {count} order(s)'})

@login_required
@user_passes_test(lambda u: u.role == 'company')
def export_orders_csv(request):
    """Export orders to CSV based on current status filter"""
    company = request.user.company_profile
    orders = Order.objects.filter(company=company).order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="orders_{status_filter or "all"}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Date', 'Customer Name', 'Customer Email', 
        'Total Amount', 'Status', 'Payment Method', 'Payment Status', 
        'Shipping Address', 'Phone', 'Tracking Number'
    ])
    
    for order in orders:
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.user.get_full_name() or order.user.email,
            order.user.email,
            order.total_amount,
            order.get_status_display(),
            order.get_payment_method_display(),
            order.get_payment_status_display(),
            f"{order.shipping_address}, {order.shipping_city}, {order.shipping_state}, {order.shipping_country}",
            order.shipping_phone,
            order.tracking_number
        ])
        
    return response