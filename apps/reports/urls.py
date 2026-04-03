from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('sales/', views.sales_report, name='sales'),
    path('products/', views.products_report, name='products'),
    path('users/', views.users_report, name='users'),
    path('download/', views.download_report, name='download'),
]