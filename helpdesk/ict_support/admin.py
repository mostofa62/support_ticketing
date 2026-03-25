from django import forms
from django.contrib import admin
from django.utils import timezone
from .models import IssueCategory, IssueSubcategory, Ticket, Attachment, PasswordResetConfig, StaffUser, ClientUser, Operation

from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin,GroupAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from users.models import UserProfile
from .admin_site import admin_site

# keep reference to original
original_get_app_list = admin.site.get_app_list

def custom_get_app_list(self, request, app_label=None):
    app_list = original_get_app_list(request, app_label)

    # ---- Reorder apps ----
    desired_app_order = ['ict_support', 'auth']
    app_list.sort(
        key=lambda x: desired_app_order.index(x['app_label'])
        if x['app_label'] in desired_app_order else 100
    )

    # ---- Reorder models inside each app ----
    model_order_map = {
        'auth': ['User', 'Group'],
        'ict_support': ['Ticket', 'IssueCategory', 'IssueSubcategory', 'PasswordResetConfig'],
    }

    for app in app_list:
        if app['app_label'] in model_order_map:
            desired_model_order = model_order_map[app['app_label']]
            app['models'].sort(
                key=lambda x: desired_model_order.index(x['object_name'])
                if x['object_name'] in desired_model_order else 100
            )

    return app_list

# ✅ bind correctly
#admin.site.get_app_list = custom_get_app_list.__get__(admin.site, type(admin.site))

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm 
    inlines = (UserProfileInline,)

    def get_inline_instances(self, request, obj=None):
        # Only show the UserProfileInline when editing an existing user
        if not obj:
            return []  # don't show inline on add page
        return super().get_inline_instances(request, obj)

    # keep the default fieldsets for User
    fieldsets = (
        (None, {'fields': ('username',)}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Change Password', {'fields': ( "password1", "password2")}),
        #('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups')}),
        #('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Important dates', {'fields': ('date_joined',)}),
    )

    # Change username label
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['username'].label = "Email"
        # Add custom error messages if you want (optional)
        form.base_fields['username'].error_messages = {
            "required": "Email is required",
            "invalid": "Enter a valid email address"
        }
        return form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 
                'first_name',
                'last_name',
                'phone_number',
                'address',
                'groups', 
                'is_staff',
                'password1', 
                'password2'
            ),
        }),
    )
    filter_horizontal = ("groups",)



#admin.site.unregister(User)
#admin.site.register(User, CustomUserAdmin)
#admin_site.unregister(User)
admin_site.register(User,CustomUserAdmin)
admin_site.register(Group,GroupAdmin)

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

#admin.site.register(IssueCategory)
admin_site.register(IssueCategory)
#admin.site.register(IssueSubcategory)
admin_site.register(IssueSubcategory)


#@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    #list_display = ('id', 'submitter', 'assigned_to', 'status', 'priority', 'date_created')
    list_display = (
        #'id',
        'view_details',
        'submitter_link',  # list display clickable
        'assigned_to',
        #'assigned_to_display',
        'status',
        #'status_badge',
        #'priority_badge',
        'priority',
        'attachment_count',
        'date_created',
        'date_resolved'
    )
    list_editable = ('assigned_to', 'status','priority', 'date_resolved')
    #exclude = ('submitter',) 
    readonly_fields = ('submitter','submitter_display',)
    ordering = ('-date_created',)

    def get_list_display(self, request):
        is_operation = request.user.groups.filter(name="Operation").exists()
        if request.user.is_superuser or is_operation:
            return self.list_display
        
        return (
            'view_details',
            'attachment_icon',
            'location',
            'status',
            #'priority',
            #'status_badge',
            'priority_badge',
            'date_created',
            'date_resolved'
        )

    
    
        

    def get_readonly_fields(self, request, obj=None):
        is_operation = request.user.groups.filter(name="Operation").exists()
        if request.user.is_superuser or is_operation:
            return self.readonly_fields

        # make ALL fields readonly for staff
        return [field.name for field in self.model._meta.fields]
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        is_operation = request.user.groups.filter(name="Operation").exists()
        if not request.user.is_superuser and not is_operation:
            extra_context = extra_context or {}
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False
            extra_context['show_save_and_add_another'] = False
            extra_context['show_delete'] = False
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def status_badge(self, obj):
        colors = {
            'open': '#dc3545',          # red
            'in_progress': '#ffc107',   # yellow
            'resolved': '#28a745',      # green
            'closed': '#6c757d',        # gray
        }
        color = colors.get(obj.status, '#000')

        return format_html(
            '<span style="padding:4px 8px; border-radius:8px; color:white; background:{};">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = "Status"

    def priority_badge(self, obj):
        colors = {
            'low': '#17a2b8',
            'medium': '#ffc107',
            'high': '#dc3545',
            'urgent':'#EE0000',
        }
        color = colors.get(obj.priority, '#000')

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            obj.get_priority_display()
        )

    priority_badge.short_description = "Priority"

    # Hide submitter in the form but keep readonly
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        # remove 'submitter' from form fields
        if 'submitter' in fields:
            fields.remove('submitter')
        return fields


    # Show submitter nicely in form view
    def submitter_display(self, obj):
        if obj.submitter:
            full_name = obj.submitter.get_full_name() or obj.submitter.username
            url = reverse('admin:auth_user_change', args=[obj.submitter.pk])
            return format_html('<a href="{}">{}</a>', url, f'{full_name} ({obj.submitter.username})')
        return "-"
    submitter_display.short_description = "Submitter"

    

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        is_operation = request.user.groups.filter(name="Operation").exists()
        # Staff only see tickets assigned to them
        if not request.user.is_superuser and not is_operation:
            qs = qs.filter(assigned_to=request.user)
        # Annotate attachments count
        qs = qs.annotate(_attachment_count=Count('attachments'))
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            staff_group = Group.objects.filter(name="Staff").first()
            if staff_group:
                kwargs["queryset"] = User.objects.filter(groups=staff_group, is_active=True)
                
                # This is the key part: show full name with username in dropdown
                class UserModelChoiceField(forms.ModelChoiceField):
                    def label_from_instance(self, obj):
                        full_name = obj.get_full_name() or obj.username
                        return f"{full_name} ({obj.username})"
                
                kwargs["form_class"] = UserModelChoiceField

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Show fullname with username in brackets
    def assigned_to_display(self, obj):
        if obj.assigned_to:
            full_name = f"{obj.assigned_to.get_full_name() or obj.assigned_to.username}"
            return f"{full_name} ({obj.assigned_to.username})"
        return "-"
    assigned_to_display.short_description = "Assigned To"

    # Show submitter in list view as clickable link
    def submitter_link(self, obj):
        if obj.submitter:
            full_name = obj.submitter.get_full_name() or obj.submitter.username
            url = reverse('admin:auth_user_change', args=[obj.submitter.pk])
            return format_html('<a href="{}">{}</a>', url, f'{full_name} ({obj.submitter.username})')
        return "-"
    submitter_link.short_description = "Submitter"
    submitter_link.admin_order_field = 'submitter'

    
    
    

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        is_operation = request.user.groups.filter(name="Operation").exists()

        # Operation can edit ANY ticket
        if is_operation:
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
        is_operation = request.user.groups.filter(name="Operation").exists()

        # For staff only (not superuser, not operation)
        if not request.user.is_superuser and not is_operation:
            if change:
                original = Ticket.objects.get(pk=obj.pk)

                # prevent changing restricted fields
                obj.assigned_to = original.assigned_to
                obj.priority = original.priority
                obj.submitter = original.submitter
            else:
                # on create
                obj.submitter = request.user

        # Ensure submitter is always set
        if not obj.submitter:
            obj.submitter = request.user

        super().save_model(request, obj, form, change)

    

    def attachment_count(self, obj):
        return obj._attachment_count

    attachment_count.short_description = "Attachments"

    def attachment_icon(self, obj):
        if obj._attachment_count > 0:
            return format_html("📎 {}", obj._attachment_count)
        return "-"

    attachment_icon.short_description = "Files"

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

admin_site.register(Ticket, TicketAdmin)

class TicketAttachmentAdmin(admin.ModelAdmin):
    pass

from solo.admin import SingletonModelAdmin
#@admin.register(PasswordResetConfig)
class PasswordResetConfigAdmin(SingletonModelAdmin):
    pass

admin_site.register(PasswordResetConfig, PasswordResetConfigAdmin)

#@admin.register(StaffUser)
class StaffUserAdmin(UserAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(groups__name="Staff")

    # disable add/edit/delete
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Customize list display — hide is_staff
    list_display = ('email', 'first_name', 'last_name', 'is_active')

    # Remove filter sidebar items
    list_filter = ('is_active',)  # empty tuple disables all default filters

admin_site.register(StaffUser, StaffUserAdmin)
#@admin.register(ClientUser, site=admin_site)
class ClientUserAdmin(UserAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(groups__name="Client")

    # disable add/edit/delete
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Customize list display — hide is_staff
    list_display = ('email', 'first_name', 'last_name', 'is_active')

    # Remove filter sidebar items
    list_filter = ('is_active',)  # empty tuple disables all default filters

admin_site.register(ClientUser, ClientUserAdmin)



#@admin.register(ClientUser, site=admin_site)
class OperationAdmin(UserAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(groups__name="Operation")

    # disable add/edit/delete
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Customize list display — hide is_staff
    list_display = ('email', 'first_name', 'last_name', 'is_active')

    # Remove filter sidebar items
    list_filter = ('is_active',)  # empty tuple disables all default filters


admin_site.register(Operation, OperationAdmin)