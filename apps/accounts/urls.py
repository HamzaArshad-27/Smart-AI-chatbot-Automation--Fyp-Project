from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # OTP Verification
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('pending-approval/<int:user_id>/', views.pending_approval, name='pending_approval_user'),
    
    # Password Reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
]