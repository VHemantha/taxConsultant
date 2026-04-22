from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('action_required', 'Action Required'),
        ('reminder', 'Reminder'),
        ('warning', 'Warning'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    related_submission_id = models.IntegerField(null=True, blank=True)
    related_client_id = models.IntegerField(null=True, blank=True)   # ClientProfile.id
    related_year_id = models.IntegerField(null=True, blank=True)     # TaxYear.id
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.recipient.email}"
