from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('tax_forms', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientAssessmentYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('notification_sent', models.BooleanField(default=False)),
                ('form_sent', models.BooleanField(default=False)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessment_years', to=settings.AUTH_USER_MODEL)),
                ('tax_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_assignments', to='tax_forms.taxyear')),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='year_assignments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'client_assessment_years',
                'ordering': ['-tax_year__year'],
            },
        ),
        migrations.AddConstraint(
            model_name='clientassessmentyear',
            constraint=models.UniqueConstraint(fields=['client', 'tax_year'], name='unique_client_year'),
        ),
    ]
