from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.http import HttpResponse
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.accounts.models import User
import csv
import openpyxl
from datetime import datetime, timedelta

@login_required
def sales_report(request):
    """Sales report"""
    # Get date range from request
    date_from = request.GET.get('from', (datetime.now() - timedelta(days=30)).date())
    date_to = request.GET.get('to', datetime.now().date())
    
    # Filter orders based on user role
    if request.user.is_admin:
        orders = Order.objects.filter(created_at__date__range=[date_from, date_to])
    elif request.user.is_company:
        orders = Order.objects.filter(
            company=request.user.company_profile,
            created_at__date__range=[date_from, date_to]
        )
    else:
        orders = Order.objects.filter(user=request.user, created_at__date__range=[date_from, date_to])
    
    # Sales data
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Daily sales
    daily_sales = orders.extra(
        {'day': "date(created_at)"}
    ).values('day').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('day')
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value,
        'daily_sales': daily_sales,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reports/sales.html', context)

@login_required
def products_report(request):
    """Products performance report"""
    if request.user.is_company:
        products = Product.objects.filter(company=request.user.company_profile)
    elif request.user.is_seller:
        products = Product.objects.filter(seller=request.user.seller_profile)
    else:
        products = Product.objects.all()
    
    # Product performance
    product_performance = products.annotate(
        total_sold=Sum('order_items__quantity'),
        total_revenue=Sum('order_items__total')
    ).order_by('-total_revenue')[:50]
    
    context = {
        'products': product_performance,
    }
    
    return render(request, 'reports/products.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def users_report(request):
    """Users report"""
    users = User.objects.all().annotate(
        total_orders=Count('orders'),
        total_spent=Sum('orders__total_amount', filter=Q(orders__status='delivered'))
    ).order_by('-total_spent')
    
    context = {
        'users': users,
        'total_users': users.count(),
    }
    
    return render(request, 'reports/users.html', context)

@login_required
def download_report(request):
    """Download report as CSV/Excel"""
    report_type = request.GET.get('type', 'sales')
    format_type = request.GET.get('format', 'csv')
    
    # Create response
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
        writer = csv.writer(response)
        
        # Write headers and data based on report type
        if report_type == 'sales':
            writer.writerow(['Date', 'Order Count', 'Revenue'])
            # Add data rows...
    else:
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{report_type.capitalize()} Report"
        # Add data...
        wb.save(response)
    
    return response


# Additional helper functions for data processing can be added here

@login_required
def dashboard_report(request):
    """Executive dashboard report"""
    # Get current month and previous month data
    today = timezone.now()
    current_month_start = today.replace(day=1, hour=0, minute=0, second=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Current month stats
    current_month_orders = Order.objects.filter(
        created_at__gte=current_month_start,
        status='delivered'
    )
    current_month_revenue = current_month_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Previous month stats
    previous_month_orders = Order.objects.filter(
        created_at__gte=previous_month_start,
        created_at__lt=current_month_start,
        status='delivered'
    )
    previous_month_revenue = previous_month_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate growth
    revenue_growth = ((current_month_revenue - previous_month_revenue) / previous_month_revenue * 100) if previous_month_revenue > 0 else 0
    
    # Top products
    top_products = OrderItem.objects.values('product__name', 'product__id').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total')
    ).order_by('-total_revenue')[:10]
    
    # Recent activity
    recent_orders = Order.objects.select_related('user', 'company').order_by('-created_at')[:10]
    
    context = {
        'current_month_revenue': current_month_revenue,
        'previous_month_revenue': previous_month_revenue,
        'revenue_growth': revenue_growth,
        'current_month_orders': current_month_orders.count(),
        'previous_month_orders': previous_month_orders.count(),
        'top_products': top_products,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'reports/dashboard.html', context)

@login_required
def category_report(request):
    """Category performance report"""
    categories = Category.objects.annotate(
        total_products=Count('products', filter=Q(products__is_active=True)),
        total_sold=Sum('products__order_items__quantity'),
        total_revenue=Sum('products__order_items__total')
    ).order_by('-total_revenue')
    
    context = {
        'categories': categories,
        'total_revenue': categories.aggregate(total=Sum('total_revenue'))['total'] or 0,
    }
    
    return render(request, 'reports/categories.html', context)

@login_required
def seller_report(request):
    """Seller performance report"""
    if request.user.is_company:
        sellers = User.objects.filter(
            role='seller',
            seller_profile__company=request.user.company_profile
        ).annotate(
            total_orders=Count('seller_profile__order_items__order', distinct=True),
            total_revenue=Sum('seller_profile__order_items__total'),
            total_products=Count('seller_profile__products', distinct=True)
        )
    else:
        sellers = User.objects.filter(role='seller').annotate(
            total_orders=Count('seller_profile__order_items__order', distinct=True),
            total_revenue=Sum('seller_profile__order_items__total'),
            total_products=Count('seller_profile__products', distinct=True)
        )
    
    context = {
        'sellers': sellers.order_by('-total_revenue'),
        'total_sellers': sellers.count(),
    }
    
    return render(request, 'reports/sellers.html', context)

@login_required
def inventory_report(request):
    """Inventory/Stock report"""
    if request.user.is_company:
        products = Product.objects.filter(company=request.user.company_profile)
    else:
        products = Product.objects.all()
    
    # Low stock products
    low_stock = products.filter(stock_quantity__lte=10, is_active=True)
    
    # Out of stock products
    out_of_stock = products.filter(stock_quantity=0, is_active=True)
    
    # Total inventory value
    inventory_value = products.aggregate(total=Sum('price'))['total'] or 0
    
    context = {
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'inventory_value': inventory_value,
        'total_products': products.count(),
        'total_stock': products.aggregate(total=Sum('stock_quantity'))['total'] or 0,
    }
    
    return render(request, 'reports/inventory.html', context)

def download_report(request):
    """Enhanced download report with multiple formats"""
    report_type = request.GET.get('type', 'sales')
    format_type = request.GET.get('format', 'csv')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    
    # Get data based on report type
    if report_type == 'sales':
        data = get_sales_data(date_from, date_to)
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d')}"
    elif report_type == 'products':
        data = get_products_data()
        filename = f"products_report_{datetime.now().strftime('%Y%m%d')}"
    elif report_type == 'users':
        data = get_users_data()
        filename = f"users_report_{datetime.now().strftime('%Y%m%d')}"
    else:
        data = []
        filename = "report"
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        writer = csv.writer(response)
        for row in data:
            writer.writerow(row)
            
    elif format_type == 'excel':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = report_type.capitalize()
        
        for row in data:
            ws.append(row)
        
        # Style the header row
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
            cell.font = openpyxl.styles.Font(color="FFFFFF")
        
        wb.save(response)
    
    return response

def get_sales_data(date_from=None, date_to=None):
    """Helper function to get sales data for export"""
    orders = Order.objects.filter(status='delivered')
    
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    data = [['Date', 'Order #', 'Customer', 'Amount', 'Status']]
    for order in orders:
        data.append([
            order.created_at.strftime('%Y-%m-%d'),
            order.order_number,
            order.user.email,
            f"${order.total_amount}",
            order.get_status_display()
        ])
    
    return data

def get_products_data(request):
    """Helper function to get products data for export"""
    products = Product.objects.filter(is_active=True)
    
    data = [['Product Name', 'SKU', 'Category', 'Price', 'Stock', 'Total Sold', 'Revenue']]
    for product in products:
        total_sold = product.order_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        revenue = product.order_items.aggregate(Sum('total'))['total__sum'] or 0
        data.append([
            product.name,
            product.sku or 'N/A',
            product.category.name if product.category else 'Uncategorized',
            f"${product.price}",
            product.stock_quantity,
            total_sold,
            f"${revenue}"
        ])
    
    return data

def get_users_data(request):
    """Helper function to get users data for export"""
    users = User.objects.all()
    
    data = [['Email', 'Role', 'Phone', 'Status', 'Joined Date', 'Total Orders', 'Total Spent']]
    for user in users:
        total_orders = user.orders.filter(status='delivered').count()
        total_spent = user.orders.filter(status='delivered').aggregate(Sum('total_amount'))['total__sum'] or 0
        data.append([
            user.email,
            user.get_role_display(),
            user.phone or 'N/A',
            'Active' if user.is_active else 'Inactive',
            user.date_joined.strftime('%Y-%m-%d'),
            total_orders,
            f"${total_spent}"
        ])
    
    return data