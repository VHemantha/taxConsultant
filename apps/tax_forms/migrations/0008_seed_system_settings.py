"""
Data migration: seed the SystemSettings record with DPR-TMS branding.
Uses update_or_create so it is safe to run multiple times.
"""
from django.db import migrations


def seed_settings(apps, schema_editor):
    SystemSettings = apps.get_model('tax_forms', 'SystemSettings')
    SystemSettings.objects.update_or_create(
        id=1,
        defaults={
            'company_name': 'DPR-TMS',
            'company_tagline': 'DPR Tax Management System | PERSONAL INCOME TAX RETURN',
            'footer_text': 'DPR-TMS | Confidential',
        },
    )


def unseed_settings(apps, schema_editor):
    pass  # non-destructive reverse


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0007_taxsubmission_foreign_income_tax'),
    ]

    operations = [
        migrations.RunPython(seed_settings, reverse_code=unseed_settings),
    ]
