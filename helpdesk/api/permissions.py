# api/permissions.py
from rest_framework.permissions import BasePermission

class IsTicketOwnerOrStaffAssigned(BasePermission):
    """
    Clients can only view/modify their own tickets.
    Staff can only view/modify tickets assigned to them.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.groups.filter(name='Staff').exists():
            return obj.assigned_to == user
        else:
            return obj.submitter == user