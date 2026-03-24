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

    
    
    editing_ticket_id = request.session.get('editing_ticket_id')
    if editing_ticket_id:
        request.session.pop('editing_ticket_id', None)
        request.session.modified = True

    
    if not request.user.userprofile.is_active_submitter:
        return redirect('dashboard')  # user is blocked from submitting tickets
    if request.method == 'POST':
        session_id = request.POST.get('session_id')

        if not session_id:
            return JsonResponse({'error': 'Missing session_id'}, status=400)
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.submitter = request.user
            ticket.save()

            # Move temp attachments
            temp_files = TempAttachment.objects.filter(
                user=request.user,
                session_id=session_id
            )

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


from ict_support.validators import validate_file_size, validate_mime_type

def get_error_message(e):
    if hasattr(e, "messages"):
        return e.messages[0]
    return str(e)

@require_POST
@login_required
def ajax_upload_attachment(request):

    # ✅ Ensure session_id exists
    session_id = request.POST.get('session_id')

    if not session_id:
        return JsonResponse({'error': 'Missing session_id'}, status=400)

    # ✅ Detect edit mode safely (frontend OR session fallback)
    ticket_id = request.POST.get('ticket_id') or request.session.get('editing_ticket_id')

    # ✅ Get temp files (STRICT isolation)
    temp_qs = TempAttachment.objects.filter(
        user=request.user,
        session_id=session_id,
        ticket_id=ticket_id
    )

    temp_count = temp_qs.count()

    # ✅ Count existing attachments if edit mode
    existing_count = 0
    if ticket_id:
        existing_count = Attachment.objects.filter(
            ticket_id=ticket_id,
            ticket__submitter=request.user
        ).count()

    total_count = temp_count + existing_count

    # ✅ Enforce max limit
    if total_count >= settings.MAX_ATTACHMENT_COUNT:
        return JsonResponse({
            'error': f'Maximum {settings.MAX_ATTACHMENT_COUNT} attachments allowed.'
        }, status=400)

    file = request.FILES.get('file')

    if not file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    # ✅ Validate file size
    try:
        validate_file_size(file)
    except Exception as e:
        return JsonResponse({'error': get_error_message(e)}, status=400)

    # ✅ Validate MIME type
    try:
        validate_mime_type(file)
    except Exception as e:
        return JsonResponse({'error': get_error_message(e)}, status=400)

    # ✅ Save temp file (session-bound)
    temp_attachment = TempAttachment.objects.create(
        user=request.user,
        session_id=session_id,
        file=file,
        ticket_id=ticket_id
    )

    return JsonResponse({
        'id': temp_attachment.id,
        'file_name': os.path.basename(temp_attachment.file.name),
        'file_url': request.build_absolute_uri(temp_attachment.file.url),
        'remaining': settings.MAX_ATTACHMENT_COUNT - (total_count + 1)
    })



@require_POST
@login_required
def ajax_delete_attachment(request, attachment_id):
    try:
        temp = TempAttachment.objects.get(
            id=attachment_id,
            user=request.user
        )

        # ✅ ALWAYS use temp.session_id
        session_id = temp.session_id

        temp.file.delete()
        temp.delete()

        # ✅ Get ticket from temp OR session safely
        ticket_id = request.POST.get('ticket_id') or request.session.get('editing_ticket_id')

        temp_count = TempAttachment.objects.filter(
            user=request.user,
            session_id=session_id,
            ticket_id=ticket_id
        ).count()

        existing_count = 0
        if ticket_id:
            existing_count = Attachment.objects.filter(
                ticket_id=ticket_id,
                ticket__submitter=request.user
            ).count()

        total = temp_count + existing_count

        remaining = settings.MAX_ATTACHMENT_COUNT - total

        return JsonResponse({
            'success': True,
            'remaining': remaining
        })

    except TempAttachment.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    
@require_POST
@login_required
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(
        Attachment,
        id=attachment_id,
        ticket__submitter=request.user
    )

    ticket_id = attachment.ticket_id

    attachment.file.delete()
    attachment.delete()

    session_id = request.POST.get('session_id')

    if not session_id:
            return JsonResponse({'error': 'Missing session_id'}, status=400)

    temp_count = TempAttachment.objects.filter(
        user=request.user,
        session_id=session_id,
        ticket_id=ticket_id
    ).count()

    existing_count = Attachment.objects.filter(
        ticket_id=ticket_id,
        ticket__submitter=request.user
    ).count()

    total = temp_count + existing_count

    remaining = settings.MAX_ATTACHMENT_COUNT - total

    return JsonResponse({
        'success': True,
        'remaining': remaining
    })


from django.shortcuts import get_object_or_404

@login_required
@group_required('Client')
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, submitter=request.user)

    if ticket.status == 'closed':
        return redirect('dashboard')

    

    # ✅ Mark editing context
    request.session['editing_ticket_id'] = ticket.id

    attachments = ticket.attachments.all()

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)

        session_id = request.POST.get('session_id')

        if not session_id:
                return JsonResponse({'error': 'Missing session_id'}, status=400)

        if form.is_valid():
            ticket = form.save()

            # ✅ ONLY get temp files for THIS session (critical fix)
            temp_files = TempAttachment.objects.filter(
                user=request.user,
                session_id=session_id,
                ticket_id=ticket_id
            )

            ticket_folder = os.path.join(
                settings.MEDIA_ROOT,
                f"{settings.TICKET_ATTACHMENT_PATH}{ticket.id}"
            )
            os.makedirs(ticket_folder, exist_ok=True)

            for temp in temp_files:
                old_path = temp.file.path

                # Extra safety (file might already be deleted)
                if not os.path.exists(old_path):
                    temp.delete()
                    continue

                filename = os.path.basename(old_path)
                new_path = os.path.join(ticket_folder, filename)

                shutil.move(old_path, new_path)

                Attachment.objects.create(
                    ticket=ticket,
                    file=f"{settings.TICKET_ATTACHMENT_PATH}{ticket.id}/{filename}"
                )

                temp.delete()

            # ✅ Clean session state (important)
            request.session.pop('editing_ticket_id', None)
            request.session.modified = True
            

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



@login_required
def attachment_remaining(request, session_id):
    

    if not session_id:
        return JsonResponse({'error': 'Missing session_id'}, status=400)

    

    ticket_id = request.session.get('editing_ticket_id')

    temp_count = TempAttachment.objects.filter(
        user=request.user,
        session_id=session_id,
        ticket_id=ticket_id
    ).count()

    existing_count = 0
    if ticket_id:
        existing_count = Attachment.objects.filter(
            ticket_id=ticket_id,
            ticket__submitter=request.user
        ).count()

    total = temp_count + existing_count

    remaining = settings.MAX_ATTACHMENT_COUNT - total

    return JsonResponse({
        'success': True,
        'remaining': remaining,
        'total':existing_count,
        'ticket_id':ticket_id
    })


@login_required
def list_temp_attachments(request,session_id):
    
    if not session_id:
        return JsonResponse({'error': 'Missing session_id'}, status=400)

    

    ticket_id = request.session.get('editing_ticket_id')

    temp_files = TempAttachment.objects.filter(
        user=request.user,
        session_id=session_id,
        ticket_id=ticket_id
    )

    
    data = [{
        'id': t.id,
        'name': t.file.name.split('/')[-1],
        'url': request.build_absolute_uri(t.file.url),
    } for t in temp_files]
    
    return JsonResponse({
        'success': True,
        'files': data
    })

@login_required
@group_required('Client')
def ticket_details(request, id):
    ticket = Ticket.objects.get(id=id)

    return JsonResponse({
        'description': ticket.description,
        'location': ticket.location,
    })