from django import forms
from django.contrib import admin
from django.utils import timezone
from .models import IssueCategory, IssueSubcategory, Ticket, Attachment, PasswordResetConfig, StaffUser, ClientUser

from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from users.models import UserProfile

original_get_app_list = admin.site.get_app_list



def custom_get_app_list(request):
    app_list = original_get_app_list(request)

    # ---- Reorder apps ----
    desired_app_order = ['ict_support','auth']  # Replace 'myapp' with your app label
    app_list.sort(
        key=lambda x: desired_app_order.index(x['app_label']) if x['app_label'] in desired_app_order else 100
    )

    # ---- Reorder models inside each app ----
    model_order_map = {
        'auth': ['User', 'Group'],
        'ict_support': ['Ticket', 'IssueCategory','IssueSubcategory','PasswordResetConfig'],  # Replace 'myapp' with your app label
    }

    for app in app_list:
        if app['app_label'] in model_order_map:
            desired_model_order = model_order_map[app['app_label']]
            app['models'].sort(
                key=lambda x: desired_model_order.index(x['object_name'])
                if x['object_name'] in desired_model_order else 100
            )

    return app_list

admin.site.get_app_list = custom_get_app_list


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



admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


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


from solo.admin import SingletonModelAdmin
@admin.register(PasswordResetConfig)
class PasswordResetConfigAdmin(SingletonModelAdmin):
    pass



@admin.register(StaffUser)
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
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')

    # Remove filter sidebar items
    list_filter = ('is_active',)  # empty tuple disables all default filters

@admin.register(ClientUser)
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
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')

    # Remove filter sidebar items
    list_filter = ('is_active',)  # empty tuple disables all default filters