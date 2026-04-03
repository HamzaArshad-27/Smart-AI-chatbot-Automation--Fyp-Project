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