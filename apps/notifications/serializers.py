from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'notification_type_display',
            'is_read', 'related_submission_id', 'related_client_id', 'related_year_id',
            'created_at', 'read_at',
        ]
        read_only_fields = ['id', 'created_at']
