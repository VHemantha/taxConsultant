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

# Create Tax Year 2025/2026
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
if created:
    print(f"Created Tax Year: {tax_year.label}")
else:
    print(f"Tax Year already exists: {tax_year.label}")

# Create default consultant
if not CustomUser.objects.filter(email='consultant@taxportal.lk').exists():
    consultant = CustomUser.objects.create_user(
        email='consultant@taxportal.lk',
        username='consultant',
        first_name='Tax',
        last_name='Consultant',
        password='Admin@12345',
        role='consultant',
    )
    print(f"Created consultant: {consultant.email} / password: Admin@12345")
else:
    print("Consultant already exists")

print("\nSetup complete!")
print("Consultant login: consultant@taxportal.lk / Admin@12345")
print("Remember to change the default password in production!")
