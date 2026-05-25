from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0011_encrypt_personal_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsubmission',
            name='payment_slip',
            field=models.FileField(blank=True, null=True, upload_to='payment_slips/%Y/%m/'),
        ),
    ]
