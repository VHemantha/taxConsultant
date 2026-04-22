"""
Data migration: seed Y/A 2020/2021 through Y/A 2024/2025 so that the
client registration screen can show the current year + 5 previous years.
Each Sri Lanka Y/A period runs April 1 → March 31 of the following year.
Skips any year that already exists (idempotent).
"""
import datetime
from decimal import Decimal
from django.db import migrations


YEARS_TO_SEED = [
    # (year_int, label, start, end)
    (2024, 'Y/A 2024/2025', datetime.date(2024, 4, 1), datetime.date(2025, 3, 31)),
    (2023, 'Y/A 2023/2024', datetime.date(2023, 4, 1), datetime.date(2024, 3, 31)),
    (2022, 'Y/A 2022/2023', datetime.date(2022, 4, 1), datetime.date(2023, 3, 31)),
    (2021, 'Y/A 2021/2022', datetime.date(2021, 4, 1), datetime.date(2022, 3, 31)),
    (2020, 'Y/A 2020/2021', datetime.date(2020, 4, 1), datetime.date(2021, 3, 31)),
]


def seed_years(apps, schema_editor):
    TaxYear = apps.get_model('tax_forms', 'TaxYear')
    existing = set(TaxYear.objects.values_list('year', flat=True))
    to_create = []
    for year_int, label, start, end in YEARS_TO_SEED:
        if year_int not in existing:
            to_create.append(TaxYear(
                year=year_int,
                label=label,
                assessment_year_start=start,
                assessment_year_end=end,
                personal_relief=Decimal('1800000.00'),
                is_active=True,
            ))
    if to_create:
        TaxYear.objects.bulk_create(to_create)


def unseed_years(apps, schema_editor):
    TaxYear = apps.get_model('tax_forms', 'TaxYear')
    TaxYear.objects.filter(year__in=[y[0] for y in YEARS_TO_SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0005_add_workflow_statuses'),
    ]

    operations = [
        migrations.RunPython(seed_years, reverse_code=unseed_years),
    ]
