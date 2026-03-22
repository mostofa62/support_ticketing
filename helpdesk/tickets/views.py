# tickets/views.py
import os
import shutil
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from django.conf import settings
from .forms import TicketForm
from ict_support.models import Attachment, Ticket
from .decorators import group_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import TempAttachment
import uuid

@never_cache
@login_required
@group_required('Client')
def create_ticket(request):
    ticket_session_id = request.session.get('ticket_session_id')
    if not ticket_session_id:
        ticket_session_id = str(uuid.uuid4())
        request.session['ticket_session_id'] = ticket_session_id
    
    if not request.user.userprofile.is_active_submitter:
        return redirect('dashboard')  # user is blocked from submitting tickets
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.submitter = request.user
            ticket.save()

            # Move temp attachments
            temp_files = TempAttachment.objects.filter(user=request.user)

            ticket_folder = os.path.join(
                settings.MEDIA_ROOT,
                f"{settings.TICKET_ATTACHMENT_PATH}{ticket.id}"
            )
            os.makedirs(ticket_folder, exist_ok=True)

            for temp in temp_files:
                old_path = temp.file.path
                filename = os.path.basename(old_path)
                new_path = os.path.join(ticket_folder, filename)

                shutil.move(old_path, new_path)

                Attachment.objects.create(
                    ticket=ticket,
                    file=f"{settings.TICKET_ATTACHMENT_PATH}{ticket.id}/{filename}"
                )

                temp.delete()
            
            
            return redirect('dashboard')
    else:
        form = TicketForm()
    return render(request, 'tickets/create_ticket.html', {'form': form, 'MAX_ATTACHMENT_COUNT':settings.MAX_ATTACHMENT_COUNT})


from django.http import JsonResponse
from ict_support.models import IssueSubcategory

def subcategories_by_category(request, category_id):
    subcategories = IssueSubcategory.objects.filter(category_id=category_id)
    data = [{'id': sc.id, 'name': sc.name} for sc in subcategories]
    return JsonResponse(data, safe=False)

from django.utils import timezone
from datetime import timedelta
from ict_support.validators import validate_file_size, validate_mime_type
@require_POST
@login_required
def ajax_upload_attachment(request):

    session_id = request.session.get('ticket_session_id')
    # Limit max 2
    if TempAttachment.objects.filter(
        user=request.user,
        session_id=session_id
    ).count() >= settings.MAX_ATTACHMENT_COUNT:
        return JsonResponse({'error': f'Maximum {settings.MAX_ATTACHMENT_COUNT} attachments allowed.'}, status=400)

    file = request.FILES.get('file')

    if not file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    # Validate file size
    try:
        validate_file_size(file)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    # Validate MIME type
    try:
        validate_mime_type(file)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    # If all validations pass, save
    temp_attachment = TempAttachment.objects.create(
        user=request.user,
        session_id=request.session.get('ticket_session_id'),
        file=file,
    )

    return JsonResponse({
        'id': temp_attachment.id,
        'file_name': os.path.basename(temp_attachment.file.name),
        'file_url': request.build_absolute_uri(temp_attachment.file.url)
    })



@require_POST
@login_required
def ajax_delete_attachment(request, attachment_id):
    try:
        temp = TempAttachment.objects.get(id=attachment_id, user=request.user)
        temp.file.delete()
        temp.delete()
        return JsonResponse({'success': True})
    except TempAttachment.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    
@require_POST
@login_required
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(Attachment, id=attachment_id, ticket__submitter=request.user)

    attachment.file.delete()
    attachment.delete()

    return JsonResponse({'success': True})


from django.shortcuts import get_object_or_404

@login_required
@group_required('Client')
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, submitter=request.user)

    if ticket.status == 'closed':
        return redirect('dashboard')  # prevent editing closed tickets
    
    attachments = ticket.attachments.all()

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)

        if form.is_valid():
            ticket = form.save()

            # Move temp attachments
            temp_files = TempAttachment.objects.filter(user=request.user)

            ticket_folder = os.path.join(
                settings.MEDIA_ROOT,
                f"{settings.TICKET_ATTACHMENT_PATH}{ticket.id}"
            )
            os.makedirs(ticket_folder, exist_ok=True)

            for temp in temp_files:
                old_path = temp.file.path
                filename = os.path.basename(old_path)
                new_path = os.path.join(ticket_folder, filename)

                shutil.move(old_path, new_path)

                Attachment.objects.create(
                    ticket=ticket,
                    file=f"{settings.TICKET_ATTACHMENT_PATH}{ticket.id}/{filename}"
                )

                temp.delete()

            return redirect('dashboard')

    else:
        form = TicketForm(instance=ticket)

    return render(request, 'tickets/create_ticket.html', {
        'form': form,
        'edit_mode': True,
        'ticket': ticket,
        'attachments': attachments,
        'MAX_ATTACHMENT_COUNT': settings.MAX_ATTACHMENT_COUNT
    })