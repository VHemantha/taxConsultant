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

print("\nSetup complete!")
print("All consultants use password: Admin@12345")
print("Remember to change default passwords in production!")
