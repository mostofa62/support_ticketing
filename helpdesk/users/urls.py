# users/urls.py
from django.urls import path
from .views import home, register, dashboard, UserLoginView
from django.contrib.auth.views import LogoutView
from .views import dashboard_data, validate_email

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/data/', dashboard_data, name='dashboard_data'),
    path("validate-email/", validate_email, name="validate_email"),
]
