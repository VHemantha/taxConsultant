from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .email_utils import send_notification_email
from .sms_utils import send_sms


@receiver(post_save, sender=Notification)
def on_notification_created(sender, instance, created, **kwargs):
    if created:
        send_notification_email(instance)
        _send_notification_sms(instance)


def _send_notification_sms(notification):
    recipient = notification.recipient
    if not recipient.phone:
        return
    text = f'{notification.title}: {notification.message}'.replace('\n', ' ').strip()
    if len(text) > 300:
        text = text[:297] + '...'
    send_sms([recipient.phone], text)
