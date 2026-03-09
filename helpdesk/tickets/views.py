# tickets/views.py
import os
import shutil
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from ict_support import settings
from .forms import TicketForm
from ict_support.models import Ticket, Notification, Attachment
from .decorators import group_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import TempAttachment


@never_cache
@login_required
@group_required('Submitter')
def create_ticket(request):
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
            
            # create notification for submitter
            Notification.objects.create(
                recipient=request.user,
                ticket=ticket,
                event_type='ticket_created',
                message_type='in_app'
            )
            return redirect('dashboard')
    else:
        form = TicketForm()
    return render(request, 'tickets/create_ticket.html', {'form': form})


from django.http import JsonResponse
from ict_support.models import IssueSubcategory

def subcategories_by_category(request, category_id):
    subcategories = IssueSubcategory.objects.filter(category_id=category_id)
    data = [{'id': sc.id, 'name': sc.name} for sc in subcategories]
    return JsonResponse(data, safe=False)



@require_POST
@login_required
def ajax_upload_attachment(request):

    # Limit max 2
    if TempAttachment.objects.filter(user=request.user).count() >= 2:
        return JsonResponse({'error': 'Maximum 2 attachments allowed.'}, status=400)

    file = request.FILES.get('file')

    if not file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    temp_attachment = TempAttachment.objects.create(
        user=request.user,
        file=file
    )

    return JsonResponse({
        'id': temp_attachment.id,
        'file_name': temp_attachment.file.name
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
