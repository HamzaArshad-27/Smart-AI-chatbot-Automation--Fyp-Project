from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('sales/', views.sales_report, name='sales'),
    path('products/', views.products_report, name='products'),
    path('users/', views.users_report, name='users'),
    path('download/', views.download_report, name='download'),
    path('api/sales/', views.sales_api, name='sales_api'),
    path('admin/', views.admin_reports, name='admin_reports'),
    path('company/', views.company_reports, name='company_reports'),
    path('customer/', views.customer_reports, name='customer_reports'),
]