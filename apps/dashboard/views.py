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
def freeze_user(request, user_id):
    """Freeze/Deactivate a user account"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        
        # Send freeze notification email
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Vendora - Account Deactivated'
        message = f"""
        Hello {user.email},
        
        Your account has been deactivated by the administrator. You cannot log in at this time.
        
        If you believe this is a mistake, please contact support.
        
        Best regards,
        Vendora Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        
        messages.success(request, f'User {user.email} account has been deactivated.')
    
    return redirect('dashboard:pending_users')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def unfreeze_user(request, user_id):
    """Unfreeze/Reactivate a user account"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = True
        user.save()
        
        # Send reactivation email
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Vendora - Account Reactivated'
        message = f"""
        Hello {user.email},
        
        Your account has been reactivated by the administrator. You can now log in again.
        
        Best regards,
        Vendora Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        
        messages.success(request, f'User {user.email} account has been reactivated.')
    
    return redirect('dashboard:all_users')


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

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def all_users(request):
    """View to list all users with filtering and search"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-date_joined')
    
    # Base queryset
    users = User.objects.all()
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True, is_approved=True)
    elif status_filter == 'pending':
        users = users.filter(is_approved=False, email_verified=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'unverified':
        users = users.filter(email_verified=False)
    
    # Apply sorting
    valid_sort_fields = ['email', 'first_name', 'last_name', 'role', 'date_joined', '-email', '-first_name', '-last_name', '-role', '-date_joined']
    if sort_by in valid_sort_fields:
        users = users.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(users, 20)  # 20 users per page
    page = request.GET.get('page', 1)
    
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    # Get counts for stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True, is_approved=True).count()
    pending_users = User.objects.filter(is_approved=False, email_verified=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    
    context = {
        'users': users_page,
        'total_users': total_users,
        'active_users': active_users,
        'pending_users': pending_users,
        'inactive_users': inactive_users,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'user_roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
            ('admin', 'Admin'),
            ('company', 'Company'),
            ('seller', 'Seller'),
            ('retailer', 'Retailer'),
            ('customer', 'Customer'),
        ],
    }
    
    return render(request, 'dashboard/all_users.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user's orders if they have any
    orders = []
    if hasattr(user, 'orders'):
        orders = user.orders.all().order_by('-created_at')[:10]
    
    # Get user's company if company role
    company = None
    if user.role == 'company' and hasattr(user, 'company_profile'):
        company = user.company_profile
    
    # Get user's seller profile if seller role
    seller = None
    if user.role == 'seller' and hasattr(user, 'seller_profile'):
        seller = user.seller_profile
    
    context = {
        'view_user': user,
        'orders': orders,
        'company': company,
        'seller': seller,
    }
    
    return render(request, 'dashboard/user_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def add_user(request):
    """Add a new user from admin panel"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'customer')
        phone = request.POST.get('phone', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_approved = request.POST.get('is_approved') == 'on'
        email_verified = request.POST.get('email_verified') == 'on'
        
        # Validation
        errors = []
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('A user with this email already exists.')
        
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if not first_name:
            errors.append('First name is required.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'dashboard/add_user.html', {
                'form_data': request.POST,
                'user_roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
                    ('admin', 'Admin'),
                    ('company', 'Company'),
                    ('seller', 'Seller'),
                    ('retailer', 'Retailer'),
                    ('customer', 'Customer'),
                ],
            })
        
        # Create user
        try:
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                phone=phone,
                is_active=is_active,
                is_approved=is_approved,
                email_verified=email_verified,
                password=make_password(password),
            )
            
            messages.success(request, f'User {email} created successfully!')
            return redirect('dashboard:user_detail', user_id=user.id)
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            return render(request, 'dashboard/add_user.html', {
                'form_data': request.POST,
                'user_roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
                    ('admin', 'Admin'),
                    ('company', 'Company'),
                    ('seller', 'Seller'),
                    ('retailer', 'Retailer'),
                    ('customer', 'Customer'),
                ],
            })
    
    context = {
        'user_roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
            ('admin', 'Admin'),
            ('company', 'Company'),
            ('seller', 'Seller'),
            ('retailer', 'Retailer'),
            ('customer', 'Customer'),
        ],
    }
    
    return render(request, 'dashboard/add_user.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def edit_user(request, user_id):
    """Edit an existing user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'customer')
        phone = request.POST.get('phone', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_approved = request.POST.get('is_approved') == 'on'
        email_verified = request.POST.get('email_verified') == 'on'
        
        # Validation
        errors = []
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exclude(id=user_id).exists():
            errors.append('A user with this email already exists.')
        
        if password and len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if not first_name:
            errors.append('First name is required.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'dashboard/edit_user.html', {
                'edit_user': user,
                'user_roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
                    ('admin', 'Admin'),
                    ('company', 'Company'),
                    ('seller', 'Seller'),
                    ('retailer', 'Retailer'),
                    ('customer', 'Customer'),
                ],
            })
        
        # Update user
        try:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.phone = phone
            user.is_active = is_active
            user.is_approved = is_approved
            user.email_verified = email_verified
            
            # Only update password if provided
            if password:
                user.password = make_password(password)
            
            user.save()
            
            messages.success(request, f'User {email} updated successfully!')
            return redirect('dashboard:user_detail', user_id=user.id)
            
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
            return render(request, 'dashboard/edit_user.html', {
                'edit_user': user,
                'user_roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
                    ('admin', 'Admin'),
                    ('company', 'Company'),
                    ('seller', 'Seller'),
                    ('retailer', 'Retailer'),
                    ('customer', 'Customer'),
                ],
            })
    
    context = {
        'edit_user': user,
        'user_roles': User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [
            ('admin', 'Admin'),
            ('company', 'Company'),
            ('seller', 'Seller'),
            ('retailer', 'Retailer'),
            ('customer', 'Customer'),
        ],
    }
    
    return render(request, 'dashboard/edit_user.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
@require_POST
def delete_user(request, user_id):
    """Delete user from database - hard delete"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard:all_users')
    
    try:
        user_email = user.email
        user.delete()
        messages.success(request, f'User {user_email} has been completely deleted from the database. They can sign up again with the same email.')
    except Exception as e:
        messages.error(request, f'Error deleting user: {str(e)}')
    
    return redirect('dashboard:all_users')


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
@require_POST
def bulk_action(request):
    """Handle bulk actions on users"""
    action = request.POST.get('action', '')
    user_ids = request.POST.getlist('user_ids[]')
    
    if not user_ids:
        messages.error(request, 'No users selected.')
        return redirect('dashboard:all_users')
    
    users = User.objects.filter(id__in=user_ids)
    
    if action == 'delete':
        # Prevent deleting yourself
        if str(request.user.id) in user_ids:
            messages.error(request, 'You cannot delete your own account. It has been excluded from bulk deletion.')
            users = users.exclude(id=request.user.id)
        
        count = users.count()
        emails = list(users.values_list('email', flat=True))
        users.delete()
        
        messages.success(request, f'{count} user(s) have been permanently deleted. They can sign up again: {", ".join(emails[:5])}{"..." if len(emails) > 5 else ""}')
    
    elif action == 'approve':
        count = users.update(is_approved=True, is_active=True)
        messages.success(request, f'{count} user(s) have been approved.')
    
    elif action == 'deactivate':
        # Don't deactivate yourself
        users = users.exclude(id=request.user.id)
        count = users.update(is_active=False)
        messages.success(request, f'{count} user(s) have been deactivated.')
    
    elif action == 'activate':
        count = users.update(is_active=True)
        messages.success(request, f'{count} user(s) have been activated.')
    
    return redirect('dashboard:all_users')


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def check_email(request):
    """AJAX endpoint to check if email exists"""
    email = request.GET.get('email', '').strip()
    user_id = request.GET.get('user_id', None)
    
    if user_id:
        exists = User.objects.filter(email=email).exclude(id=user_id).exists()
    else:
        exists = User.objects.filter(email=email).exists()
    
    return JsonResponse({'exists': exists})