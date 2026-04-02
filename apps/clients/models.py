from django.db import models
from django.conf import settings


class ClientProfile(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('pending_review', 'Pending Consultant Review'),
        ('awaiting_confirmation', 'Awaiting Client Confirmation'),
        ('archived', 'Archived'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    assigned_consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients'
    )
    full_name = models.CharField(max_length=200)
    tin = models.CharField(max_length=50, blank=True, null=True, verbose_name='TIN')
    pin = models.CharField(max_length=50, blank=True, null=True, verbose_name='PIN')
    nic_passport = models.CharField(max_length=50, blank=True, null=True, verbose_name='NIC/Passport')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='not_started')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_profiles'
        verbose_name = 'Client Profile'
        verbose_name_plural = 'Client Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"
