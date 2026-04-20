"""
Run this script after migrations to create initial data:
  python manage.py shell < create_initial_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import date
from apps.tax_forms.models import TaxYear
from apps.authentication.models import CustomUser

# ── Tax Year 2025/2026 ────────────────────────────────────────────────────────
tax_year, created = TaxYear.objects.get_or_create(
    year=2026,
    defaults={
        'label': 'Y/A 2025/2026',
        'assessment_year_start': date(2025, 4, 1),
        'assessment_year_end': date(2026, 3, 31),
        'personal_relief': 1800000.00,
        'is_active': True,
    }
)
print(f"{'Created' if created else 'Exists'} Tax Year: {tax_year.label}")

# ── Consultants ───────────────────────────────────────────────────────────────
CONSULTANTS = [
    {
        'email': 'consultant@taxportal.lk',
        'username': 'consultant',
        'first_name': 'Tax',
        'last_name': 'Consultant',
        'password': 'Admin@12345',
    },
    {
        'email': 'ashan@taxportal.lk',
        'username': 'ashan',
        'first_name': 'Ashan',
        'last_name': 'Perera',
        'password': 'Admin@12345',
    },
    {
        'email': 'nimal@taxportal.lk',
        'username': 'nimal',
        'first_name': 'Nimal',
        'last_name': 'Silva',
        'password': 'Admin@12345',
    },
    {
        'email': 'kumari@taxportal.lk',
        'username': 'kumari',
        'first_name': 'Kumari',
        'last_name': 'Fernando',
        'password': 'Admin@12345',
    },
]

for c in CONSULTANTS:
    if not CustomUser.objects.filter(email=c['email']).exists():
        user = CustomUser.objects.create_user(
            email=c['email'],
            username=c['username'],
            first_name=c['first_name'],
            last_name=c['last_name'],
            password=c['password'],
            role='consultant',
        )
        print(f"Created consultant: {user.email} / {c['password']}")
    else:
        print(f"Exists: {c['email']}")

# ── Accounts Division ─────────────────────────────────────────────────────────
ACCOUNTS_USERS = [
    {
        'email': 'accounts@taxportal.lk',
        'username': 'accounts',
        'first_name': 'Accounts',
        'last_name': 'Officer',
        'password': 'Admin@12345',
    },
]

for a in ACCOUNTS_USERS:
    if not CustomUser.objects.filter(email=a['email']).exists():
        user = CustomUser.objects.create_user(
            email=a['email'],
            username=a['username'],
            first_name=a['first_name'],
            last_name=a['last_name'],
            password=a['password'],
            role='accounts_division',
        )
        print(f"Created accounts officer: {user.email} / {a['password']}")
    else:
        print(f"Exists: {a['email']}")

# ── Super Admin ───────────────────────────────────────────────────────────────
SUPER_ADMINS = [
    {
        'email': 'superadmin@taxportal.lk',
        'username': 'superadmin',
        'first_name': 'Super',
        'last_name': 'Admin',
        'password': 'Admin@12345',
    },
]

for sa in SUPER_ADMINS:
    if not CustomUser.objects.filter(email=sa['email']).exists():
        user = CustomUser.objects.create_user(
            email=sa['email'],
            username=sa['username'],
            first_name=sa['first_name'],
            last_name=sa['last_name'],
            password=sa['password'],
            role='super_admin',
        )
        print(f"Created super admin: {user.email} / {sa['password']}")
    else:
        print(f"Exists: {sa['email']}")

print("\nSetup complete!")
print("All users use password: Admin@12345")
print("Remember to change default passwords in production!")
