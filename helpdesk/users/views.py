# users/views.py

from email.utils import localtime
import random

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.utils import timezone

from .models import PasswordResetOTP
from notifications.services.notification_service import create_notification

from .forms import CustomSetPasswordForm, PasswordResetChoiceForm, PasswordResetRequestForm, ProfileUpdateForm, RegisterForm, LoginForm, SetNewPasswordForm
from ict_support.models import Ticket
from .decorators import group_required
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib import messages
# -----------------------------
# Public home page
# -----------------------------
@never_cache
def home(request):
    return render(request, 'users/home.html')


# -----------------------------
# Registration view
# -----------------------------
@never_cache
@transaction.atomic
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # 🔥 authenticate using email + password
            user = authenticate(
                request,
                username=user.email,  # because your EmailBackend expects username=email
                password=form.cleaned_data["password1"]
            )
            
            create_notification(
                user=user,
                event_type="user_registered",
                channel="email",
                data={
                    "full_name": user.get_full_name(),
                    "email": user.email,
                    "message": "Thank you for registering! You can now submit support tickets and track their status."
                }
            )

            if user is not None:
                login(request, user)

            return redirect("dashboard")

    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


# -----------------------------
# Login view
# -----------------------------
@method_decorator(never_cache, name='dispatch')
class UserLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = LoginForm

    def form_valid(self, form):
        """Override to handle 'remember me'."""
        # Log the user in
        user = form.get_user()
        login(self.request, user)

        # Handle 'remember me'
        remember = form.cleaned_data.get('remember_me')
        if remember:
            # Session will expire in 30 days
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            # Session expires on browser close
            self.request.session.set_expiry(0)

        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user

        if user.groups.filter(name='Client').exists():
            return reverse_lazy('dashboard')

        return reverse_lazy('admin:index')


# -----------------------------
# Logout view (FULL session destroy)
# -----------------------------
@never_cache
def user_logout(request):
    request.session.flush()   # completely destroys session
    logout(request)
    return redirect('login')


# -----------------------------
# Dashboard (Client only)
# -----------------------------
@never_cache
@login_required
@group_required('Client')
def dashboard(request):
    profile = request.user.userprofile
    tickets = Ticket.objects.filter(
        submitter=request.user
    ).order_by('-date_created')

    

    can_submit = getattr(profile, 'is_active_submitter', True)

    return render(request, 'users/dashboard.html', {
        'tickets': tickets,
        'can_submit': can_submit
    })


# -----------------------------
# Dashboard AJAX Data
# -----------------------------
@never_cache
@login_required
@group_required('Client')
def dashboard_data(request):
    qs = Ticket.objects.filter(
        submitter=request.user
    ).order_by('-date_created')

    data = []

    for t in qs:
        data.append({
            'id': t.id,
            'category': getattr(t.category, 'name', ''),
            'subcategory': getattr(t.subcategory, 'name', ''),
            'status': t.get_status_display(),
            'date_created': t.date_created.strftime('%Y-%m-%d %H:%M') if t.date_created else '',
            'detail_url': request.build_absolute_uri(
                t.get_absolute_url()
            ) if hasattr(t, 'get_absolute_url') else ''
        })

    return JsonResponse(data, safe=False)


def validate_email(request):
    email = request.GET.get("username", None)

    if User.objects.filter(username=email).exists():
        return JsonResponse(False, safe=False)

    return JsonResponse(True, safe=False)


@login_required
def profile(request):

    if request.method == "POST":
        form = ProfileUpdateForm(
            request.POST,
            user=request.user,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = ProfileUpdateForm(
            user=request.user,
            instance=request.user
        )

    return render(request, "users/profile.html", {"form": form})



@login_required
def change_password(request):
    if request.method == "POST":
        form = CustomSetPasswordForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()

            # keep user logged in
            update_session_auth_hash(request, user)

            messages.success(request, "Password changed successfully!")
            return redirect("password_change")
    else:
        form = CustomSetPasswordForm(request.user)

    return render(request, "users/password_change.html", {"form": form})


from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetChoiceForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data['method']
            value = form.cleaned_data['email_or_phone']

            if method == 'email':
                user = User.objects.get(email=value)

                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                create_notification(
                    user=user,
                    event_type='password_reset',
                    channel='email',
                    data={
                        'full_name': user.get_full_name(),
                        'email': user.email,
                        'reset_link': request.build_absolute_uri(
                            reverse_lazy('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                        )
                    }
                )
                messages.success(request, "Password reset instructions will be sent via email notifications.")

            else:  # SMS
                user = User.objects.get(userprofile__phone_number=value)
                otp = f"{random.randint(100000, 999999)}"
                PasswordResetOTP.objects.create(
                    user=user,
                    phone_number=user.userprofile.phone_number,
                    otp=otp
                )

                create_notification(
                    user=user,
                    event_type='password_reset_sms',
                    channel='sms',
                    data={
                        'full_name': user.get_full_name(),
                        'phone_number': user.userprofile.phone_number,
                        'otp': otp
                    }
                )
                messages.success(request, "OTP sent to your phone number.")
                request.session['reset_phone'] = user.userprofile.phone_number
                return redirect('password_reset_verify_otp')

            return redirect('login')
    else:
        form = PasswordResetChoiceForm()
    return render(request, 'users/password_reset_choice.html', {'form': form})
# Step 2: Reset password confirmation
def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "Invalid or expired link.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.password = make_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, "Password has been reset successfully.")
            return redirect('login')
    else:
        form = SetNewPasswordForm()

    return render(request, 'users/password_reset_confirm.html', {'form': form})



def password_reset_verify_otp(request):
    phone = request.session.get('reset_phone')
    if not phone:
        return redirect('password_reset_request')

    user = User.objects.get(userprofile__phone_number=phone)
    otp_obj = PasswordResetOTP.objects.filter(user=user, used=False).last()

    if request.method == "POST":
        otp = request.POST.get("otp")
        if otp_obj and otp_obj.otp == otp and otp_obj.expired_at > timezone.now():
            otp_obj.used = True
            otp_obj.save()
            request.session['reset_user_id'] = user.id
            request.session['otp_verified'] = True
            return redirect('password_reset_new_password')
        messages.error(request, "Invalid or expired OTP")

    context = {}
    if otp_obj:
        # Convert to string for JS
        context['otp_expiry'] = localtime(otp_obj.expired_at).strftime('%Y-%m-%d %H:%M:%S')

    return render(request, "users/verify_otp.html", context)


def password_reset_new_password(request):
    user_id = request.session.get('reset_user_id')
    verified = request.session.get('otp_verified')

    if not user_id or not verified:
        messages.error(request, "User not verified.")
        return redirect('password_reset_request')

    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.password = make_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, "Password has been reset successfully.")
            return redirect('login')
    else:
        form = SetNewPasswordForm()

    return render(request, "users/password_reset_confirm.html", {'form': form})