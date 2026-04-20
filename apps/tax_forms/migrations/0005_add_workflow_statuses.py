from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0004_phase2_fields_and_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsubmission',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('submitted', 'Submitted'),
                    ('info_requested', 'Information Requested'),
                    ('under_review', 'Under Consultant Review'),
                    ('calculation_done', 'Calculation Done'),
                    ('awaiting_confirmation', 'Awaiting Client Confirmation'),
                    ('confirmed', 'Client Confirmed'),
                    ('awaiting_client_review', 'Awaiting Client Review'),
                    ('client_confirmed', 'Client Confirmed (Final)'),
                    ('archived', 'Archived'),
                ],
                default='draft',
                max_length=30,
            ),
        ),
    ]
