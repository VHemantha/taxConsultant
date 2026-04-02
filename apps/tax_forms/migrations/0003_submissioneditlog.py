from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0002_allow_blank_charfields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionEditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(max_length=100)),
                ('action', models.CharField(choices=[('update', 'Updated'), ('add', 'Added Row'), ('delete', 'Deleted Row')], default='update', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('old_data', models.JSONField(blank=True, null=True)),
                ('new_data', models.JSONField(blank=True, null=True)),
                ('edited_at', models.DateTimeField(auto_now_add=True)),
                ('edited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='form_edits', to=settings.AUTH_USER_MODEL)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='edit_logs', to='tax_forms.taxsubmission')),
            ],
            options={
                'db_table': 'submission_edit_logs',
                'ordering': ['-edited_at'],
            },
        ),
    ]
