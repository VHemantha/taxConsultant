from django.contrib.auth.models import AbstractUser
from django.db import models

from encrypted_fields import EncryptedCharField


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('consultant', 'Consultant'),          # legacy / handling person
        ('handling_person', 'Handling Person'), # explicit new role
        ('admin', 'Admin'),
        ('accounts_division', 'Accounts Division'),
        ('super_admin', 'Super Admin'),
    ]

    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = EncryptedCharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    must_change_password = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_consultant(self):
        return self.role in ('consultant', 'handling_person')

    @property
    def is_client(self):
        return self.role == 'client'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_accounts_division(self):
        return self.role == 'accounts_division'

    @property
    def is_handling_person(self):
        return self.role in ('consultant', 'handling_person')

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
