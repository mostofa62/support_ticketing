from django import forms
from django.contrib import admin
from django.utils import timezone
from .models import IssueCategory, IssueSubcategory, Ticket, Attachment, PasswordResetConfig

from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # 🔥 Auto generate username
        today = timezone.now().strftime('%Y%m%d')
        count = User.objects.filter(
            date_joined__date=timezone.now().date()
        ).count() + 1

        user.username = f"st{today}{count}"

        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

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