from django.contrib.admin import AdminSite
from django.urls import path
from django.db.models import Count
from django.template.response import TemplateResponse
from .models import Ticket
from collections import Counter
from .choices import TicketPriority,TicketStatus
class MyAdminSite(AdminSite):
    site_header = "ICT Support Admin"
    site_title = "ICT Support"
    index_title = "Welcome ICT Support"
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'operations-dashboard/',
                self.admin_view(self.operations_dashboard),
                name="operations-dashboard"
            )
        ]
        return custom_urls + urls

    # 🔥 Shared dashboard data (IMPORTANT)
    def get_dashboard_context(self, request):
        total_tickets = Ticket.objects.count()

        STATUS_COLORS = {
            'open': '#dc3545',          # red
            'in_progress': '#ffc107',   # yellow
            'resolved': '#28a745',      # green
            'closed': '#6c757d',        # gray
        }


        status_stats_raw = Ticket.objects.values('status').annotate(count=Count('id'))

        status_stats = [
            {
                "label": TicketStatus(s["status"]).label,  # 🔥 converts to "Open", "In Progress"
                "count": s["count"],
                "color": STATUS_COLORS.get(s["status"], '#999999')
            }
            for s in status_stats_raw
        ]

        PRIORITY_COLORS = {
            'low': '#17a2b8',
            'medium': '#ffc107',
            'high': '#dc3545',
            'urgent': '#EE0000',
        }
        
        priority_stats_raw = (
            Ticket.objects.values('priority')
            .annotate(count=Count('id'))
        )

        priority_stats = [
            {
                "label": TicketPriority(p["priority"]).label,
                "count": p["count"],
                "color": PRIORITY_COLORS.get(p["priority"], '#999999')
            }
            for p in priority_stats_raw
        ]

        return dict(
            self.each_context(request),
            total_tickets=total_tickets,
            status_stats=status_stats,
            priority_stats=priority_stats,
            open_tickets=Ticket.objects.filter(status='open'),
            in_progress=Ticket.objects.filter(status='in_progress'),
            resolved=Ticket.objects.filter(status='resolved'),
        )

    # 🔐 Dashboard page
    def operations_dashboard(self, request):
        if not (
            request.user.is_superuser or
            request.user.groups.filter(name__in=["Staff", "Operations"]).exists()
        ):
            return TemplateResponse(request, "admin/403.html", status=403)

        context = self.get_dashboard_context(request)

        return TemplateResponse(request, "admin/operations_dashboard.html", context)

    # 🚀 DEFAULT DASHBOARD (after login)
    def index(self, request, extra_context=None):
        if request.user.groups.filter(name__in=["Staff", "Operations"]).exists():
            context = self.get_dashboard_context(request)

            return TemplateResponse(
                request,
                "admin/operations_dashboard.html",
                context
            )

        return super().index(request, extra_context)

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)

        # ---- Reorder apps ----
        desired_app_order = ['ict_support', 'auth']
        app_list.sort(
            key=lambda x: desired_app_order.index(x['app_label'])
            if x['app_label'] in desired_app_order else 100
        )

        # ---- Reorder models ----
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


# ✅ instance
admin_site = MyAdminSite(name="myadmin")