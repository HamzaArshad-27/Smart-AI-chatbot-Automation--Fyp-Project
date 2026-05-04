from django.conf import settings
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.urls import reverse
from django.db import IntegrityError
from django.core.mail import EmailMessage
from apps.companies.models import Company
from .models import User, OTP
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm,
    OTPVerificationForm, ForgotPasswordForm, ResetPasswordForm
)
import logging

logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(user, otp_code, purpose='verification'):
    """Send OTP email with proper error handling"""
    
    if purpose == 'verification':
        subject = 'Vendora - Email Verification OTP'
        message = f"""
Hello {user.get_full_name() or user.email},

Thank you for registering with Vendora!

Your email verification OTP is: {otp_code}

This OTP is valid for 10 minutes.

If you didn't create an account, please ignore this email.

Best regards,
Vendora Team
"""
    else:
        subject = 'Vendora - Password Reset OTP'
        message = f"""
Hello {user.get_full_name() or user.email},

You requested a password reset for your Vendora account.

Your password reset OTP is: {otp_code}

This OTP is valid for 10 minutes.

If you didn't request this, please ignore this email.

Best regards,
Vendora Team
"""
    
    print(f"\n{'='*60}")
    print(f"📧 OTP for {user.email}")
    print(f"   Purpose: {purpose}")
    print(f"   Code: {otp_code}")
    print(f"   DEV_MODE: {settings.DEV_MODE}")
    print(f"{'='*60}\n")
    
    if settings.DEV_MODE:
        return True
    
    try:
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #e5e5e5; border-radius: 10px;">
            <h2 style="color: #5b5fe3;">Vendora</h2>
            <p>Hello <strong>{user.get_full_name() or user.email}</strong>,</p>
            <p>Your OTP for {purpose} is:</p>
            <div style="background: #f5f3f0; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <span style="font-size: 28px; font-weight: bold; letter-spacing: 5px; color: #5b5fe3;">{otp_code}</span>
            </div>
            <p style="color: #737373; font-size: 13px;">This OTP is valid for 10 minutes.</p>
            <hr style="border: none; border-top: 1px solid #e5e5e5;">
            <p style="color: #a3a3a3; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </div>
        """
        
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=from_email,
            to=recipient_list,
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        print(f"❌ Email sending failed: {str(e)}")
        return False


def get_redirect_url(user):
    """Get the appropriate redirect URL based on user role"""
    role_redirects = {
        'admin': 'dashboard:admin',
        'company': 'dashboard:company',
        'seller': 'dashboard:seller',
        'retailer': 'dashboard:retailer',
        'customer': 'dashboard:customer',
    }
    return reverse(role_redirects.get(user.role, 'dashboard:index'))


def create_company_profile(user, form_data=None):
    """Create or get company profile for a user"""
    try:
        company, created = Company.objects.get_or_create(
            user=user,
            defaults={
                'name': form_data.get('company_name', user.email.split('@')[0]) if form_data else user.email.split('@')[0],
                'email': user.email,
                'phone': form_data.get('company_phone', '') if form_data else '',
                'address': form_data.get('company_address', '') if form_data else '',
                'website': form_data.get('company_website', '') if form_data else '',
                'registration_number': f"REG-{user.id:06d}",
                'is_active': True
            }
        )
        return company
    except IntegrityError:
        return Company.objects.get(user=user)
    except Exception as e:
        print(f"Error creating company: {e}")
        return None


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = True
                
                # ✅ NO MORE APPROVAL NEEDED - Auto approve everyone
                if settings.DEV_MODE:
                    # Dev mode: skip OTP, directly login
                    user.email_verified = True
                    user.is_approved = True
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    
                    if user.role == 'company':
                        create_company_profile(user, form.cleaned_data)
                    
                    messages.success(request, f'✅ Account created successfully! You can now login.')
                    return redirect('accounts:login')
                
                else:
                    # Production: Send OTP, auto-approve after verification
                    user.email_verified = False
                    user.is_approved = True  # ✅ Auto-approved - no admin needed!
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    
                    if user.role == 'company':
                        create_company_profile(user, form.cleaned_data)
                    
                    # Generate and send OTP
                    otp_code = generate_otp()
                    OTP.objects.create(
                        user=user,
                        code=otp_code,
                        expires_at=timezone.now() + timezone.timedelta(minutes=10)
                    )
                    send_otp_email(user, otp_code, 'verification')
                    
                    request.session['pending_user_id'] = user.id
                    
                    messages.success(request, '✅ Registration successful! Please verify your email with the OTP sent.')
                    return redirect('accounts:verify_otp')
                    
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {
        'form': form,
        'dev_mode': settings.DEV_MODE
    })


def verify_otp(request):
    """OTP verification view - After OTP, user can login directly"""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.warning(request, 'Please login or register first.')
        return redirect('accounts:login')
    
    user = get_object_or_404(User, id=user_id)
    
    # If already verified, go straight to login
    if user.email_verified:
        del request.session['pending_user_id']
        messages.success(request, '✅ Email already verified. Please login.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            
            if settings.DEV_MODE:
                if len(otp_code) == 6 and otp_code.isdigit():
                    user.email_verified = True
                    user.save()
                    del request.session['pending_user_id']
                    
                    # ✅ Auto-login after OTP verification
                    login(request, user)
                    messages.success(request, f'✅ Email verified! Welcome {user.get_full_name() or user.email}!')
                    return redirect(get_redirect_url(user))
                else:
                    messages.error(request, 'Please enter a valid 6-digit OTP.')
            
            else:
                otp = OTP.objects.filter(
                    user=user,
                    code=otp_code,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if otp:
                    otp.is_used = True
                    otp.save()
                    user.email_verified = True
                    user.save()
                    del request.session['pending_user_id']
                    
                    # ✅ Auto-login after OTP verification
                    login(request, user)
                    messages.success(request, f'✅ Email verified! Welcome {user.get_full_name() or user.email}!')
                    return redirect(get_redirect_url(user))
                else:
                    messages.error(request, '❌ Invalid or expired OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'email': user.email,
        'dev_mode': settings.DEV_MODE
    })


def resend_otp(request):
    """Resend OTP to user"""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.warning(request, 'Session expired. Please register again.')
        return redirect('accounts:register')
    
    user = get_object_or_404(User, id=user_id)
    
    OTP.objects.filter(user=user, is_used=False).update(is_used=True)
    
    otp_code = generate_otp()
    OTP.objects.create(
        user=user,
        code=otp_code,
        expires_at=timezone.now() + timezone.timedelta(minutes=10)
    )
    send_otp_email(user, otp_code, 'verification')
    
    messages.success(request, '📧 New OTP has been sent to your email.')
    return redirect('accounts:verify_otp')


def login_view(request):
    """Login view - Simplified, no approval check needed"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, email=email, password=password)
            
            if user:
                # Dev mode auto-fix
                if settings.DEV_MODE:
                    user.is_approved = True
                    user.email_verified = True
                    user.save()
                
                # ✅ Only check email verification and active status
                if not user.email_verified:
                    request.session['pending_user_id'] = user.id
                    messages.error(request, '⚠️ Please verify your email first. Check your inbox for OTP.')
                    return redirect('accounts:verify_otp')
                
                if not user.is_active:
                    messages.error(request, '🚫 Your account has been deactivated. Contact support.')
                    return redirect('accounts:login')
                
                # ✅ Login directly - no approval check!
                login(request, user)
                
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                
                messages.success(request, f'👋 Welcome back, {user.get_full_name() or user.email}!')
                
                next_url = request.GET.get('next', '')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect(get_redirect_url(user))
            else:
                messages.error(request, '❌ Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'dev_mode': settings.DEV_MODE
    })


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, '👋 You have been logged out successfully.')
    return redirect('core:home')


# ============================================
# PASSWORD MANAGEMENT (Unchanged)
# ============================================

def forgot_password(request):
    """Forgot password - send OTP"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            
            try:
                user = User.objects.get(email=email)
                OTP.objects.filter(user=user, is_used=False).update(is_used=True)
                otp_code = generate_otp()
                
                if settings.DEV_MODE:
                    request.session['reset_user_id'] = user.id
                    request.session['reset_otp'] = otp_code
                    print(f"\n🔑 DEV MODE: Password reset OTP for {email}: {otp_code}\n")
                    messages.success(request, f'🔧 Dev Mode: Your OTP is {otp_code}')
                    return redirect('accounts:reset_password')
                else:
                    OTP.objects.create(
                        user=user,
                        code=otp_code,
                        expires_at=timezone.now() + timezone.timedelta(minutes=10)
                    )
                    send_otp_email(user, otp_code, 'reset')
                    request.session['reset_user_id'] = user.id
                    messages.success(request, '📧 Password reset OTP sent to your email.')
                    return redirect('accounts:reset_password')
                    
            except User.DoesNotExist:
                messages.error(request, '❌ No account found with this email address.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'accounts/forgot_password.html', {
        'form': form,
        'dev_mode': settings.DEV_MODE
    })


def reset_password(request):
    """Reset password with OTP"""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.warning(request, 'Session expired. Please request a new password reset.')
        return redirect('accounts:forgot_password')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            new_password = form.cleaned_data['new_password']
            verified = False
            
            if settings.DEV_MODE:
                stored_otp = request.session.get('reset_otp')
                if stored_otp and stored_otp == otp_code:
                    verified = True
            else:
                otp = OTP.objects.filter(
                    user=user,
                    code=otp_code,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).first()
                if otp:
                    otp.is_used = True
                    otp.save()
                    verified = True
            
            if verified:
                user.set_password(new_password)
                user.save()
                
                if 'reset_user_id' in request.session:
                    del request.session['reset_user_id']
                if 'reset_otp' in request.session:
                    del request.session['reset_otp']
                
                messages.success(request, '✅ Password reset successfully! Please login with your new password.')
                return redirect('accounts:login')
            else:
                messages.error(request, '❌ Invalid or expired OTP. Please try again.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {
        'form': form,
        'email': user.email,
        'dev_mode': settings.DEV_MODE
    })


# ============================================
# PROFILE MANAGEMENT
# ============================================

@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'profile_user': request.user,
        'company': getattr(request.user, 'company_profile', None),
        'seller': getattr(request.user, 'seller_profile', None),
    }
    
    return render(request, 'accounts/profile.html', context)