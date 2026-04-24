from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
import json
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.accounts.models import User
from apps.companies.models import Company, Seller
from django.contrib import messages
from django.shortcuts import get_object_or_404

@login_required
def dashboard_index(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.is_superuser or request.user.role == 'admin':
        return redirect('dashboard:admin')
    elif request.user.role == 'company':
        return redirect('dashboard:company')
    elif request.user.role == 'seller':
        return redirect('dashboard:seller')
    elif request.user.role == 'retailer':
        return redirect('dashboard:retailer')
    else:
        return redirect('dashboard:customer')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def admin_dashboard(request):
    """Admin dashboard with analytics"""
    # Get date ranges
    today = timezone.now().date()
    
    # Statistics
    total_users = User.objects.count()
    pending_approvals = User.objects.filter(is_approved=False, email_verified=True).count()
    total_companies = User.objects.filter(role='company').count()
    total_sellers = User.objects.filter(role='seller').count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    
    # Sales analytics - Fixed: Use different name for annotation
    total_revenue = Order.objects.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Top products - Fixed: Use different annotation name
    top_products = Product.objects.filter(
        order_items__order__status='delivered'
    ).annotate(
        items_sold=Sum('order_items__quantity')  # Changed from 'total_sold' to 'items_sold'
    ).order_by('-items_sold')[:10]
    
    # Monthly sales data for chart
    monthly_sales = []
    for i in range(5, -1, -1):  # Last 6 months
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        # Calculate month end
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        sales = Order.objects.filter(
            created_at__date__range=[month_start, month_end],
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_sales.append({
            'month': month_start.strftime('%B'),
            'sales': float(sales)
        })
    
    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Recent orders count by status
    orders_by_status = {
        'pending': Order.objects.filter(status='pending').count(),
        'approved': Order.objects.filter(status='approved').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    context = {
        'total_users': total_users,
        'pending_approvals': pending_approvals,
        'total_companies': total_companies,
        'total_sellers': total_sellers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'monthly_sales': json.dumps(monthly_sales),
        'recent_users': recent_users,
        'orders_by_status': orders_by_status,
    }
    
    return render(request, 'dashboard/admin.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'company')
def company_dashboard(request):
    """Company dashboard"""
    try:
        company = request.user.company_profile
    except:
        return render(request, 'dashboard/error.html', {'message': 'Company profile not found'})
    
    # Statistics
    total_sellers = company.sellers.filter(is_active=True).count()
    total_products = company.products.count()
    total_orders = company.orders.filter(status='delivered').count()
    total_revenue = company.orders.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Pending orders
    pending_orders = company.orders.filter(status='pending').count()
    
    # Recent orders
    recent_orders = company.orders.select_related('user').order_by('-created_at')[:10]
    
    # Low stock products - Fixed: Use F expression correctly
    low_stock = company.products.filter(
        stock_quantity__lte=F('low_stock_threshold')
    )[:10]
    
    # Sales by month
    monthly_sales = []
    today = timezone.now().date()
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        sales = company.orders.filter(
            created_at__date__range=[month_start, month_end],
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_sales.append({
            'month': month_start.strftime('%B'),
            'sales': float(sales)
        })
    
    context = {
        'company': company,
        'total_sellers': total_sellers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'monthly_sales': json.dumps(monthly_sales),
    }
    
    return render(request, 'dashboard/company.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'seller')
def seller_dashboard(request):
    """Seller dashboard"""
    try:
        seller = request.user.seller_profile
    except:
        return render(request, 'dashboard/error.html', {'message': 'Seller profile not found'})
    
    # Products managed by seller
    products = seller.products.filter(is_active=True)
    total_products = products.count()
    
    # Orders processed
    orders_processed = OrderItem.objects.filter(
        seller=seller,
        order__status='delivered'
    ).count()
    
    # Revenue
    revenue = OrderItem.objects.filter(
        seller=seller,
        order__status='delivered'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Pending orders to process
    pending_orders = OrderItem.objects.filter(
        seller=seller,
        status='pending'
    ).count()
    
    # Recent order items
    recent_order_items = OrderItem.objects.filter(
        seller=seller
    ).select_related('order', 'product').order_by('-created_at')[:10]
    
    context = {
        'seller': seller,
        'total_products': total_products,
        'orders_processed': orders_processed,
        'revenue': revenue,
        'pending_orders': pending_orders,
        'products': products[:10],
        'recent_order_items': recent_order_items,
    }
    
    return render(request, 'dashboard/seller.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'retailer')
def retailer_dashboard(request):
    """Retailer dashboard"""
    orders = request.user.orders.all()
    delivered_orders = orders.filter(status='delivered')
    
    total_orders = orders.count()
    total_delivered = delivered_orders.count()
    total_spent = delivered_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    average_order_value = total_spent / total_delivered if total_delivered > 0 else 0
    
    # Orders by status
    orders_by_status = {
        'pending': orders.filter(status='pending').count(),
        'approved': orders.filter(status='approved').count(),
        'processing': orders.filter(status='processing').count(),
        'shipped': orders.filter(status='shipped').count(),
        'delivered': total_delivered,
        'cancelled': orders.filter(status='cancelled').count(),
    }
    
    context = {
        'total_orders': total_orders,
        'total_spent': total_spent,
        'average_order_value': average_order_value,
        'orders_by_status': orders_by_status,
        'recent_orders': orders.select_related('company').order_by('-created_at')[:10],
    }
    
    return render(request, 'dashboard/retailer.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'customer')
def customer_dashboard(request):
    """Customer dashboard"""
    orders = request.user.orders.all()
    delivered_orders = orders.filter(status='delivered')
    
    total_orders = orders.count()
    total_spent = delivered_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = orders.select_related('company').order_by('-created_at')[:5]
    
    context = {
        'total_orders': total_orders,
        'total_spent': total_spent,
        'recent_orders': recent_orders,
        'user': request.user,
    }
    
    return render(request, 'dashboard/customer.html', context)




@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def pending_users(request):
    """View pending user approvals"""
    pending_users_list = User.objects.filter(
        is_approved=False, 
        email_verified=True
    ).order_by('-date_joined')
    
    context = {
        'pending_users': pending_users_list,
        'total_pending': pending_users_list.count(),
    }
    
    return render(request, 'dashboard/pending_users.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def approve_user(request, user_id):
    """Approve a user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_approved = True
        user.save()
        
        # Send approval email
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Vendora - Account Approved'
        message = f"""
        Hello {user.email},
        
        Your account has been approved by the administrator.
        You can now log in to your dashboard.
        
        Login URL: {settings.SITE_URL}/accounts/login/
        
        Best regards,
        Vendora Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        
        messages.success(request, f'User {user.email} has been approved successfully!')
    
    return redirect('dashboard:pending_users')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def reject_user(request, user_id):
    """Reject a user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Send rejection email
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Vendora - Account Rejected'
        message = f"""
        Hello {user.email},
        
        Your account registration has been rejected by the administrator.
        
        If you believe this is a mistake, please contact support.
        
        Best regards,
        Vendora Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        
        # Delete the user account
        user.delete()
        
        messages.success(request, f'User has been rejected and removed.')
    
    return redirect('dashboard:pending_users')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def all_users(request):
    """View all users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filter by approval status
    approved_filter = request.GET.get('approved')
    if approved_filter == 'approved':
        users = users.filter(is_approved=True)
    elif approved_filter == 'pending':
        users = users.filter(is_approved=False)
    
    context = {
        'users': users,
        'total_users': users.count(),
        'current_role': role_filter,
        'current_approved': approved_filter,
    }
    
    return render(request, 'dashboard/all_users.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def toggle_user_status(request, user_id):
    """Activate/deactivate user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f'User {user.email} has been {status}.')
    
    return redirect('dashboard:all_users')