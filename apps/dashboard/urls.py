from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('admin/pending-users/', views.pending_users, name='pending_users'),
    path('admin/approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('admin/reject-user/<int:user_id>/', views.reject_user, name='reject_user'),
    path('admin/freeze-user/<int:user_id>/', views.freeze_user, name='freeze_user'),
    path('admin/unfreeze-user/<int:user_id>/', views.unfreeze_user, name='unfreeze_user'),
    path('admin/all-users/', views.all_users, name='all_users'),
    path('admin/toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('company/', views.company_dashboard, name='company'),
    path('seller/', views.seller_dashboard, name='seller'),
    path('retailer/', views.retailer_dashboard, name='retailer'),
    path('customer/', views.customer_dashboard, name='customer'),
        # User CRUD Management
    path('users/', views.all_users, name='all_users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # User management utilities
    path('users/bulk-action/', views.bulk_action, name='bulk_action'),
    path('check-email/', views.check_email, name='check_email'),
]