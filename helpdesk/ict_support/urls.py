"""
URL configuration for ict_support project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
# Adds site header, site title, index title to the admin side.
admin.site.site_header = 'ICT Support Admin'
admin.site.site_title = 'ICT Support'
admin.site.index_title = 'Welcome ICT Support'

from ict_support.forms import AdminLoginForm

admin.site.login_form = AdminLoginForm

# Optional: Custom admin logout view
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_logout(request):
    logout(request)
    return redirect('/admin/login/')


urlpatterns = [
    path('admin/logout/', admin_logout, name='admin_logout'),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('tickets/', include('tickets.urls')),
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )