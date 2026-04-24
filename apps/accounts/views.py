# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth import login, authenticate, logout
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.core.mail import send_mail
# from django.utils import timezone
# from django.conf import settings
# from django.urls import reverse
# import random
# import string

# from .models import User, OTP
# from .forms import (
#     UserRegistrationForm, UserLoginForm, UserProfileForm,
#     OTPVerificationForm, ForgotPasswordForm, ResetPasswordForm
# )

# def generate_otp():
#     return ''.join(random.choices(string.digits, k=6))

# def send_otp_email(user, otp_code):
#     subject = 'Vendora - Email Verification OTP'
#     message = f"""
#     Hello {user.email},
    
#     Your OTP for email verification is: {otp_code}
    
#     This OTP is valid for 10 minutes.
    
#     If you didn't request this, please ignore this email.
    
#     Best regards,
#     Vendora Team
#     """
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
# def register(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard:index')
    
#     if request.method == 'POST':
#         form = UserRegistrationForm(request.POST, request.FILES)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_active = True
#             user.email_verified = False
#             user.is_approved = False
#             user.set_password(form.cleaned_data['password'])
#             user.save()
            
#             # Handle company profile if role is company
#             if user.role == 'company':
#                 from apps.companies.models import Company
#                 company = Company.objects.get(user=user)
#                 company.name = form.cleaned_data.get('company_name', user.email.split('@')[0])
#                 company.address = form.cleaned_data.get('company_address', '')
#                 company.phone = form.cleaned_data.get('company_phone', '')
#                 company.website = form.cleaned_data.get('company_website', '')
#                 company.email = user.email
#                 company.save()
            
#             # Generate and send OTP
#             otp_code = generate_otp()
#             OTP.objects.create(
#                 user=user,
#                 code=otp_code,
#                 expires_at=timezone.now() + timezone.timedelta(minutes=10)
#             )
#             send_otp_email(user, otp_code)
            
#             # Store user ID in session for OTP verification
#             request.session['pending_user_id'] = user.id
            
#             messages.success(request, 'Registration successful! Please verify your email with OTP.')
#             return redirect('accounts:verify_otp')
#     else:
#         form = UserRegistrationForm()
    
#     return render(request, 'accounts/register.html', {'form': form})
# def verify_otp(request):
#     user_id = request.session.get('pending_user_id')
#     if not user_id:
#         return redirect('accounts:login')
    
#     user = get_object_or_404(User, id=user_id)
    
#     if request.method == 'POST':
#         form = OTPVerificationForm(request.POST)
#         if form.is_valid():
#             otp_code = form.cleaned_data['otp']
#             otp = OTP.objects.filter(
#                 user=user,
#                 code=otp_code,
#                 is_used=False,
#                 expires_at__gt=timezone.now()
#             ).first()
            
#             if otp:
#                 otp.is_used = True
#                 otp.save()
#                 user.email_verified = True
#                 user.save()
                
#                 # Clear session
#                 del request.session['pending_user_id']
                
#                 messages.success(request, 'Email verified successfully! Please wait for admin approval.')
#                 return redirect('accounts:login')
#             else:
#                 messages.error(request, 'Invalid or expired OTP.')
#     else:
#         form = OTPVerificationForm()
    
#     return render(request, 'accounts/verify_otp.html', {'form': form, 'email': user.email})

# def login_view(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard:index')  # Changed from 'dashboard:index'
    
#     if request.method == 'POST':
#         form = UserLoginForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
#             user = authenticate(request, email=email, password=password)
            
#             if user:
#                 if not user.email_verified:
#                     messages.error(request, 'Please verify your email first.')
#                 elif not user.is_approved:
#                     messages.error(request, 'Your account is pending admin approval.')
#                 elif not user.is_active:
#                     messages.error(request, 'Your account is deactivated.')
#                 else:
#                     login(request, user)
#                     messages.success(request, f'Welcome back, {user.email}!')
                    
#                     # Redirect based on role
#                     next_url = request.GET.get('next', 'dashboard:index')
#                     return redirect(next_url)
#             else:
#                 messages.error(request, 'Invalid email or password.')
#     else:
#         form = UserLoginForm()
    
#     return render(request, 'accounts/login.html', {'form': form})
# @login_required
# def logout_view(request):
#     logout(request)
#     messages.success(request, 'You have been logged out successfully.')
#     return redirect('core:home')  # Changed from 'home' to 'core:home'
# @login_required
# def profile(request):
#     if request.method == 'POST':
#         form = UserProfileForm(request.POST, request.FILES, instance=request.user)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Profile updated successfully!')
#             return redirect('accounts:profile')
#     else:
#         form = UserProfileForm(instance=request.user)
    
#     return render(request, 'accounts/profile.html', {'form': form})

# def forgot_password(request):
#     if request.method == 'POST':
#         form = ForgotPasswordForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             try:
#                 user = User.objects.get(email=email)
#                 otp_code = generate_otp()
#                 OTP.objects.filter(user=user, is_used=False).update(is_used=True)
#                 OTP.objects.create(
#                     user=user,
#                     code=otp_code,
#                     expires_at=timezone.now() + timezone.timedelta(minutes=10)
#                 )
                
#                 subject = 'Vendora - Password Reset OTP'
#                 message = f"""
#                 Hello {user.email},
                
#                 Your OTP for password reset is: {otp_code}
                
#                 This OTP is valid for 10 minutes.
                
#                 If you didn't request this, please ignore this email.
                
#                 Best regards,
#                 Vendora Team
#                 """
#                 send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                
#                 request.session['reset_user_id'] = user.id
#                 messages.success(request, 'OTP sent to your email for password reset.')
#                 return redirect('accounts:reset_password')
#             except User.DoesNotExist:
#                 messages.error(request, 'No account found with this email.')
#     else:
#         form = ForgotPasswordForm()
    
#     return render(request, 'accounts/forgot_password.html', {'form': form})

# def reset_password(request):
#     user_id = request.session.get('reset_user_id')
#     if not user_id:
#         return redirect('accounts:forgot_password')
    
#     user = get_object_or_404(User, id=user_id)
    
#     if request.method == 'POST':
#         form = ResetPasswordForm(request.POST)
#         if form.is_valid():
#             otp_code = form.cleaned_data['otp']
#             new_password = form.cleaned_data['new_password']
            
#             otp = OTP.objects.filter(
#                 user=user,
#                 code=otp_code,
#                 is_used=False,
#                 expires_at__gt=timezone.now()
#             ).first()
            
#             if otp:
#                 otp.is_used = True
#                 otp.save()
#                 user.set_password(new_password)
#                 user.save()
                
#                 del request.session['reset_user_id']
                
#                 messages.success(request, 'Password reset successfully! Please login with your new password.')
#                 return redirect('accounts:login')
#             else:
#                 messages.error(request, 'Invalid or expired OTP.')
#     else:
#         form = ResetPasswordForm()
    
#     return render(request, 'accounts/reset_password.html', {'form': form, 'email': user.email})






#  for dummmy testing
from django.conf import settings
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone

from apps.companies.models import Company
from .models import User, OTP
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm,
    OTPVerificationForm, ForgotPasswordForm, ResetPasswordForm
)
@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')  # Changed from 'home' to 'core:home'
def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(user, otp_code):
    """Send OTP email - with development mode bypass"""
    if settings.DEV_MODE:
        # In dev mode, just print to console
        print(f"\n{'='*50}")
        print(f"DEVELOPMENT MODE: OTP for {user.email} is: {otp_code}")
        print(f"{'='*50}\n")
        return
    
    # Real email sending code
    subject = 'Vendora - Email Verification OTP'
    message = f"""
    Hello {user.email},
    
    Your OTP for email verification is: {otp_code}
    
    This OTP is valid for 10 minutes.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    Vendora Team
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            
            # In development mode, auto-verify and auto-approve
            if settings.DEV_MODE:
                user.email_verified = True
                user.is_approved = True
                user.set_password(form.cleaned_data['password'])
                user.save()
                
                # Create company profile if needed
                if user.role == 'company':
                    from apps.companies.models import Company
                    Company.objects.get_or_create(
                        user=user,
                        defaults={
                            "name": form.cleaned_data.get('company_name', user.email.split('@')[0]),
                            "email": user.email,
                            "registration_number": f"REG{user.id:06d}",
                            "is_active": True
                        }
                    )
                
                messages.success(request, f'Registration successful! You can now login with email: {user.email}')
                return redirect('accounts:login')
            else:
                # Normal flow with email verification
                user.email_verified = False
                user.is_approved = False
                user.set_password(form.cleaned_data['password'])
                user.save()
                
                # Handle company profile creation for pending approval
                if user.role == 'company':
                    from apps.companies.models import Company
                    Company.objects.create(
                        user=user,
                        name=form.cleaned_data.get('company_name', user.email.split('@')[0]),
                        email=user.email,
                        registration_number=f"REG{user.id:06d}",
                        is_active=False
                    )
                
                # Generate and send OTP
                otp_code = generate_otp()
                OTP.objects.create(
                    user=user,
                    code=otp_code,
                    expires_at=timezone.now() + timezone.timedelta(minutes=10)
                )
                send_otp_email(user, otp_code)
                
                # Store user ID in session for OTP verification
                request.session['pending_user_id'] = user.id
                
                messages.success(request, 'Registration successful! Please verify your email with OTP.')
                return redirect('accounts:verify_otp')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form, 'dev_mode': settings.DEV_MODE})

def verify_otp(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('accounts:login')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            
            # In development mode, accept any 6-digit OTP
            if settings.DEV_MODE:
                if len(otp_code) == 6 and otp_code.isdigit():
                    user.email_verified = True
                    user.save()
                    del request.session['pending_user_id']
                    
                    messages.success(request, 'Email verified successfully! Please wait for admin approval.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'Please enter a valid 6-digit OTP.')
            else:
                # Normal OTP verification
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
                    
                    messages.success(request, 'Email verified successfully! Please wait for admin approval.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'Invalid or expired OTP.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': user.email, 'dev_mode': settings.DEV_MODE})

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # In development mode, auto-generate OTP without email
                if settings.DEV_MODE:
                    otp_code = generate_otp()
                    print(f"\n{'='*50}")
                    print(f"DEVELOPMENT MODE: Password reset OTP for {email} is: {otp_code}")
                    print(f"{'='*50}\n")
                    
                    # Store OTP in session for verification
                    request.session['reset_user_id'] = user.id
                    request.session['reset_otp'] = otp_code
                    messages.success(request, f'Development Mode: Your OTP is {otp_code}')
                    return redirect('accounts:reset_password')
                else:
                    # Normal flow with email
                    otp_code = generate_otp()
                    OTP.objects.filter(user=user, is_used=False).update(is_used=True)
                    OTP.objects.create(
                        user=user,
                        code=otp_code,
                        expires_at=timezone.now() + timezone.timedelta(minutes=10)
                    )
                    
                    subject = 'Vendora - Password Reset OTP'
                    message = f"""
                    Hello {user.email},
                    
                    Your OTP for password reset is: {otp_code}
                    
                    This OTP is valid for 10 minutes.
                    
                    If you didn't request this, please ignore this email.
                    
                    Best regards,
                    Vendora Team
                    """
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                    
                    request.session['reset_user_id'] = user.id
                    messages.success(request, 'OTP sent to your email for password reset.')
                    return redirect('accounts:reset_password')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'accounts/forgot_password.html', {'form': form, 'dev_mode': settings.DEV_MODE})

def reset_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('accounts:forgot_password')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            new_password = form.cleaned_data['new_password']
            
            # In development mode, check against session OTP
            if settings.DEV_MODE:
                stored_otp = request.session.get('reset_otp')
                if stored_otp and stored_otp == otp_code:
                    user.set_password(new_password)
                    user.save()
                    
                    del request.session['reset_user_id']
                    if 'reset_otp' in request.session:
                        del request.session['reset_otp']
                    
                    messages.success(request, 'Password reset successfully! Please login with your new password.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'Invalid OTP.')
            else:
                # Normal OTP verification
                otp = OTP.objects.filter(
                    user=user,
                    code=otp_code,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if otp:
                    otp.is_used = True
                    otp.save()
                    user.set_password(new_password)
                    user.save()
                    
                    del request.session['reset_user_id']
                    
                    messages.success(request, 'Password reset successfully! Please login with your new password.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'Invalid or expired OTP.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {'form': form, 'email': user.email, 'dev_mode': settings.DEV_MODE})



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            
            if user:
                # In dev mode, auto-approve if needed
                if settings.DEV_MODE and not user.is_approved:
                    user.is_approved = True
                    user.save()
                    messages.info(request, 'Development Mode: User auto-approved.')
                
                if not user.email_verified:
                    messages.error(request, 'Please verify your email first.')
                elif not user.is_approved:
                    messages.error(request, 'Your account is pending admin approval.')
                elif not user.is_active:
                    messages.error(request, 'Your account is deactivated.')
                else:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.email}!')
                    
                    # Redirect based on role
                    next_url = request.GET.get('next', 'dashboard:index')
                    return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form, 'dev_mode': settings.DEV_MODE})