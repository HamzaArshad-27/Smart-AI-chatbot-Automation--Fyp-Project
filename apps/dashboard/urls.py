from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('admin/pending-users/', views.pending_users, name='pending_users'),
    path('admin/approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('admin/reject-user/<int:user_id>/', views.reject_user, name='reject_user'),
    path('admin/all-users/', views.all_users, name='all_users'),
    path('admin/toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('company/', views.company_dashboard, name='company'),
    path('seller/', views.seller_dashboard, name='seller'),
    path('retailer/', views.retailer_dashboard, name='retailer'),
    path('customer/', views.customer_dashboard, name='customer'),
]