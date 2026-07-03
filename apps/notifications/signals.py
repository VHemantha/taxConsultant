from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .email_utils import send_notification_email


@receiver(post_save, sender=Notification)
def on_notification_created(sender, instance, created, **kwargs):
    if created:
        send_notification_email(instance)
