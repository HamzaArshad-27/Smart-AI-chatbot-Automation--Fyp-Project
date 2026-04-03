from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Company, Seller
from apps.accounts.models import User
from .forms import CompanyForm, SellerForm
import json
from django.db.models import Sum, F
from datetime import timedelta

@login_required
@user_passes_test(lambda u: u.role == 'company')
def company_dashboard(request):
    """Company dashboard"""
    # Check if company profile exists, create if not
    try:
        company = request.user.company_profile
    except:
        # Create company profile if it doesn't exist
        from apps.companies.models import Company
        company = Company.objects.create(
            user=request.user,
            name=request.user.email.split('@')[0],
            email=request.user.email,
            registration_number=f"REG{request.user.id:06d}",
            is_active=request.user.is_approved
        )
    
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
    
    # Low stock products
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
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Company, Seller
from apps.accounts.models import User
from .forms import SellerForm

def company_list(request):
    """List all companies"""
    companies = Company.objects.filter(is_active=True)
    return render(request, 'companies/list.html', {'companies': companies})

def company_detail(request, company_id):
    """Company detail page"""
    company = get_object_or_404(Company, id=company_id, is_active=True)
    products = company.products.filter(is_active=True)[:12]
    return render(request, 'companies/detail.html', {'company': company, 'products': products})

@login_required
@user_passes_test(lambda u: u.role == 'company')
def manage_sellers(request):
    """Manage company sellers"""
    try:
        company = request.user.company_profile
        sellers = company.sellers.select_related('user').all()
        return render(request, 'companies/manage_sellers.html', {'sellers': sellers, 'company': company})
    except:
        messages.error(request, 'Company profile not found')
        return redirect('dashboard:index')

@login_required
@user_passes_test(lambda u: u.role == 'company')
def add_seller(request):
    """Add a new seller to company"""
    try:
        company = request.user.company_profile
    except:
        messages.error(request, 'Company profile not found')
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = SellerForm(request.POST)
        if form.is_valid():
            # Create user account for seller
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'] or 'temp123456',
                role='seller',
                is_approved=True,
                email_verified=True
            )
            
            # Create seller profile
            seller = Seller.objects.create(
                user=user,
                company=company,
                employee_id=form.cleaned_data['employee_id'],
                department=form.cleaned_data['department'],
                position=form.cleaned_data['position'],
                hire_date=form.cleaned_data['hire_date']
            )
            
            messages.success(request, f'Seller {user.email} added successfully!')
            return redirect('companies:manage_sellers')
    else:
        form = SellerForm()
    
    return render(request, 'companies/add_seller.html', {'form': form, 'company': company})

@login_required
@user_passes_test(lambda u: u.role == 'company')
def edit_seller(request, seller_id):
    """Edit an existing seller"""
    try:
        company = request.user.company_profile
        seller = get_object_or_404(Seller, id=seller_id, company=company)
    except:
        messages.error(request, 'Seller not found')
        return redirect('companies:manage_sellers')
    
    if request.method == 'POST':
        form = SellerForm(request.POST)
        if form.is_valid():
            # Update user account
            user = seller.user
            user.email = form.cleaned_data['email']
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Update seller profile
            seller.employee_id = form.cleaned_data['employee_id']
            seller.department = form.cleaned_data['department']
            seller.position = form.cleaned_data['position']
            seller.hire_date = form.cleaned_data['hire_date']
            seller.save()
            
            messages.success(request, f'Seller {user.email} updated successfully!')
            return redirect('companies:manage_sellers')
    else:
        # Pre-populate form with existing data
        initial_data = {
            'email': seller.user.email,
            'employee_id': seller.employee_id,
            'department': seller.department,
            'position': seller.position,
            'hire_date': seller.hire_date,
        }
        form = SellerForm(initial=initial_data)
    
    return render(request, 'companies/edit_seller.html', {'form': form, 'company': company, 'seller': seller})

@login_required
@user_passes_test(lambda u: u.role == 'company')
def delete_seller(request, seller_id):
    """Delete a seller"""
    try:
        company = request.user.company_profile
        seller = get_object_or_404(Seller, id=seller_id, company=company)
    except:
        messages.error(request, 'Seller not found')
        return redirect('companies:manage_sellers')
    
    if request.method == 'POST':
        user = seller.user
        seller.delete()
        user.delete()  # Delete the associated user account
        messages.success(request, 'Seller deleted successfully!')
        return redirect('companies:manage_sellers')
    
    return render(request, 'companies/delete_seller.html', {'seller': seller, 'company': company})