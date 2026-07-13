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


def _resolve_recipient_phone(user):
    """
    User.phone is a separate, optional field that's rarely filled in — the
    number a client actually gives us lives on their ClientProfile (mobile /
    telephone). Prefer User.phone (covers staff created with a phone number),
    then fall back to the client's profile.
    """
    if user.phone:
        return user.phone
    profile = getattr(user, 'client_profile', None)
    if profile:
        return profile.mobile or profile.telephone or None
    return None


def _send_notification_sms(notification):
    """
    Sends the SMS and stashes the outcome on the (in-memory) notification
    instance as `_sms_result`: True (sent), False (attempted, failed), or
    None (no phone number on file — nothing attempted). Since post_save fires
    synchronously on the same instance the caller holds, code that just called
    Notification.objects.create(...) can read this back immediately via
    getattr(notification, '_sms_result', None) — e.g. to report the outcome
    in an API response.
    """
    recipient = notification.recipient
    phone = _resolve_recipient_phone(recipient)
    if not phone:
        notification._sms_result = None
        return None
    text = f'{notification.title}: {notification.message}'.replace('\n', ' ').strip()
    if len(text) > 300:
        text = text[:297] + '...'
    result = send_sms([phone], text)
    notification._sms_result = result
    return result
