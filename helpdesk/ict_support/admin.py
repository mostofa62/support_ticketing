from django.contrib import admin
from .models import IssueCategory, IssueSubcategory, Ticket, StaffMember, Attachment, Notification

from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import User, Group

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0  # show 1 empty attachment row
    #readonly_fields = ('file_link', 'date_uploaded')
    #fields = ('file_link', 'date_uploaded')
    fields = ('file',)
    '''
    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.file.url,
                obj.file.name
            )
        return "-"
    
    file_link.short_description = "File"
    '''

admin.site.register(IssueCategory)
admin.site.register(IssueSubcategory)
#admin.site.register(StaffMember)
#admin.site.register(Notification)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    #list_display = ('id', 'submitter', 'assigned_to', 'status', 'priority', 'date_created')
    list_display = (
        'id',
        'submitter',
        'assigned_to',
        'status',
        'priority',
        'attachment_count',
        'date_created',
        'view_details'
    )
    #exclude = ('submitter',) 
    readonly_fields = ('submitter',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Staff only see tickets assigned to them
        if not request.user.is_superuser:
            qs = qs.filter(assigned_to=request.user)
        # Annotate attachments count
        qs = qs.annotate(_attachment_count=Count('attachments'))
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            # Exclude users in the "Submitter" group
            submitter_group = Group.objects.filter(name="Submitter").first()
            if submitter_group:
                kwargs["queryset"] = User.objects.exclude(groups=submitter_group)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Staff can change tickets only if assigned to them
        return obj.assigned_to == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return False  # hide bulk delete
        # Staff can delete tickets only if assigned to them
        return obj.assigned_to == request.user

    
    # Disable bulk delete for staff
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser and 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def save_model(self, request, obj, form, change):
        if not change or not obj.submitter:
            obj.submitter = request.user
        super().save_model(request, obj, form, change)

    

    def attachment_count(self, obj):
        return obj._attachment_count

    attachment_count.short_description = "Attachments"

    def view_details(self, obj):
        url = reverse(
            'admin:ict_support_ticket_change',
            args=[obj.pk]
        )
        return format_html('<a class="button" href="{}">View</a>', url)

    view_details.short_description = "Details"
    search_fields = ('submitter__username', 'description')
    list_filter = ('status', 'priority', 'category')
    inlines = [AttachmentInline]

class TicketAttachmentAdmin(admin.ModelAdmin):
    pass
