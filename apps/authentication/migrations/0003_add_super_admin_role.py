from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_add_new_roles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[
                    ('client', 'Client'),
                    ('consultant', 'Consultant'),
                    ('handling_person', 'Handling Person'),
                    ('admin', 'Admin'),
                    ('accounts_division', 'Accounts Division'),
                    ('super_admin', 'Super Admin'),
                ],
                default='client',
                max_length=20,
            ),
        ),
    ]
