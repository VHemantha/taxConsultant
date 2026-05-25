from django.db import models
from django.conf import settings

from encrypted_fields import EncryptedCharField, EncryptedTextField


class ClientAssessmentYear(models.Model):
    """Tracks which assessment years are assigned to each client for the cyclic process."""
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessment_years'
    )
    tax_year = models.ForeignKey(
        'tax_forms.TaxYear',
        on_delete=models.CASCADE,
        related_name='client_assignments'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='year_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(default=False)
    form_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'client_assessment_years'
        unique_together = ['client', 'tax_year']
        ordering = ['-tax_year__year']

    def __str__(self):
        return f"{self.client.email} — {self.tax_year.label}"


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
    full_name = EncryptedCharField(max_length=200)
    tin = EncryptedCharField(max_length=50, blank=True, null=True, verbose_name='TIN')
    pin = EncryptedCharField(max_length=50, blank=True, null=True, verbose_name='PIN')
    nic_passport = EncryptedCharField(max_length=50, blank=True, null=True, verbose_name='NIC/Passport')
    telephone = EncryptedCharField(max_length=20, blank=True, null=True)
    mobile = EncryptedCharField(max_length=20, blank=True, null=True)
    address = EncryptedTextField(blank=True, null=True)
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
