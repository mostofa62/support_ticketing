# tickets/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_ticket, name='create_ticket'),
    path('subcategories/<int:category_id>/', views.subcategories_by_category, name='subcategories_by_category'),
    path('ajax/upload/', views.ajax_upload_attachment, name='ajax_upload'),
    path('ajax/delete/<int:attachment_id>/', views.ajax_delete_attachment, name='ajax_delete'),

]