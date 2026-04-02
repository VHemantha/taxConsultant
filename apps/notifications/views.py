from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Notification
from .serializers import NotificationSerializer
from apps.clients.models import ClientProfile


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        unread_only = self.request.query_params.get('unread', None)
        if unread_only == 'true':
            qs = qs.filter(is_read=False)
        return qs


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            notifications = Notification.objects.filter(id=pk, recipient=request.user)
        else:
            notifications = Notification.objects.filter(recipient=request.user, is_read=False)

        notifications.update(is_read=True, read_at=timezone.now())
        return Response({'message': 'Notifications marked as read.'})


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'count': count})


class SendReminderView(APIView):
    """Consultant sends manual reminder to a client."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'consultant':
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        client_profile_id = request.data.get('client_id')
        message = request.data.get('message', '')

        try:
            profile = ClientProfile.objects.get(id=client_profile_id, assigned_consultant=request.user)
        except ClientProfile.DoesNotExist:
            return Response({'error': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        Notification.objects.create(
            recipient=profile.user,
            title='Reminder from Your Tax Consultant',
            message=message or 'Please complete and submit your tax form at your earliest convenience.',
            notification_type='reminder',
        )

        return Response({'message': f'Reminder sent to {profile.full_name}.'})
