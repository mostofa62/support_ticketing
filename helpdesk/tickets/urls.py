# tickets/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_ticket, name='create_ticket'),
    path('subcategories/<int:category_id>/', views.subcategories_by_category, name='subcategories_by_category'),
    path('ajax/upload/', views.ajax_upload_attachment, name='ajax_upload'),
    path('ajax/delete/<int:attachment_id>/', views.ajax_delete_attachment, name='ajax_delete'),
    path('edit/<int:ticket_id>/', views.edit_ticket, name='edit_ticket'),
    path('delete-attchment/<int:attachment_id>/',views.delete_attachment, name='delete_attachment'),
    path('attachment/remaining/<str:session_id>/', views.attachment_remaining, name='attachment_remaining'),
    path('attachment/remaining-list/<str:session_id>/', views.list_temp_attachments, name='list_temp_attachments'),
    path('tickets/<int:id>/details/', views.ticket_details, name='ticket_details')
]