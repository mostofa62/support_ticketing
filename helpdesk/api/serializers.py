from django.contrib.auth.models import User
from rest_framework import serializers
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']

from ict_support.models import Ticket, Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'file_url', 'file_type', 'file_size', 'date_uploaded']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None
    

class TicketSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    submitter_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    class Meta:
        model = Ticket
        fields = [
            'id',
            'submitter',           # still keep ID if needed
            'submitter_name',      # full name
            'assigned_to',         # ID of assigned user
            'assigned_to_name',    # full name of assigned staff
            'category_name',
            'subcategory_name',
            'priority',
            'status',
            'location',
            'description',
            'date_created',
            'date_resolved',
            'last_updated',
            'attachments',  # attachments included here
        ]
        read_only_fields = ['submitter', 'date_created', 'last_updated', 'date_resolved']

    def get_submitter_name(self, obj):
        return obj.submitter.get_full_name() or obj.submitter.username

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None
    



