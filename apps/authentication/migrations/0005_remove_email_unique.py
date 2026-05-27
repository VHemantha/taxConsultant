from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_encrypt_phone_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254),
        ),
    ]
