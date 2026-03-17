from django.contrib.auth.models import User
from rest_framework import viewsets
# Serializers define the API representation.
from .serializers import UserSerializer, TicketSerializer
from .permissions import IsTicketOwnerOrStaffAssigned
from rest_framework.permissions import IsAuthenticated
from ict_support.models import Ticket
# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsTicketOwnerOrStaffAssigned]

    def get_queryset(self):
        """
        Role-based queryset:
        - Staff: only tickets assigned to them
        - Client: only tickets submitted by them
        """
        user = self.request.user
        if user.groups.filter(name='Staff').exists():
            return Ticket.objects.filter(assigned_to=user).order_by('-date_created')
        else:
            return Ticket.objects.filter(submitter=user).order_by('-date_created')

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in user as the submitter.
        """
        serializer.save(submitter=self.request.user)