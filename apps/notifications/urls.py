from django.urls import path
from .views import NotificationListView, MarkReadView, UnreadCountView, SendReminderView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications'),
    path('unread-count/', UnreadCountView.as_view(), name='unread_count'),
    path('mark-read/', MarkReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/mark-read/', MarkReadView.as_view(), name='mark_read'),
    path('send-reminder/', SendReminderView.as_view(), name='send_reminder'),
]
