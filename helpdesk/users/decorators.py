# users/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def group_required(group_name):
    def check(user):
        return user.is_authenticated and user.groups.filter(name=group_name).exists()
    return user_passes_test(check, login_url='login')  # redirect to login if not
