# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from .forms import RegisterForm, LoginForm
from ict_support.models import Ticket, Notification
from .decorators import group_required


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

        if user.groups.filter(name='Submitter').exists():
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
# Dashboard (Submitter only)
# -----------------------------
@never_cache
@login_required
@group_required('Submitter')
def dashboard(request):
    profile = request.user.userprofile
    tickets = Ticket.objects.filter(
        submitter=request.user
    ).order_by('-date_created')

    notifications = Notification.objects.filter(
        recipient=request.user,
        status=False
    ).order_by('-date_sent')

    can_submit = getattr(profile, 'is_active_submitter', True)

    return render(request, 'users/dashboard.html', {
        'tickets': tickets,
        'notifications': notifications,
        'can_submit': can_submit
    })


# -----------------------------
# Dashboard AJAX Data
# -----------------------------
@never_cache
@login_required
@group_required('Submitter')
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
