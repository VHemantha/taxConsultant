from django.db import migrations
import encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_add_super_admin_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='phone',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
    ]
