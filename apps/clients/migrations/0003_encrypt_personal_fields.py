from django.db import migrations
import encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_clientassessmentyear'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientprofile',
            name='full_name',
            field=encrypted_fields.EncryptedCharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='tin',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=50, null=True, verbose_name='TIN'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='pin',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=50, null=True, verbose_name='PIN'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='nic_passport',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=50, null=True, verbose_name='NIC/Passport'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='telephone',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='mobile',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
    ]
