# users/urls.py
from django.urls import path

# from .forms import CustomPasswordChangeForm
from .views import home, password_reset_confirm, password_reset_new_password, password_reset_request, password_reset_verify_otp, register, dashboard, UserLoginView
from django.contrib.auth.views import LogoutView
from .views import dashboard_data, validate_email, profile, change_password
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/data/', dashboard_data, name='dashboard_data'),
    path("validate-email/", validate_email, name="validate_email"),
    path("profile/", profile, name="profile"),
    path("password-change/", change_password, name="password_change"),
    # '''
    # path(
    #     "password-change/",
    #     auth_views.PasswordChangeView.as_view(
    #         template_name="users/password_change.html",
    #         form_class=CustomPasswordChangeForm
    #     ),
    #     name="password_change",
    # ),
    # path(
    #     "password-change-done/",
    #     auth_views.PasswordChangeDoneView.as_view(
    #         template_name="users/password_change_done.html"
    #     ),
    #     name="password_change_done",
    # ),
    # '''
    path('password-reset/verify-otp/', password_reset_verify_otp, name='password_reset_verify_otp'),
    path('password-reset/new-password/', password_reset_new_password , name='password_reset_new_password'),
    path('reset-password/', password_reset_request, name='password_reset_request'),
    path('reset-password-confirm/<str:uidb64>/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
    
]
