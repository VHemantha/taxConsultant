from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0014_cashflow_other_items'),
    ]

    operations = [
        migrations.CreateModel(
            name='TBSecuritiesIncome',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gross_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15)),
                ('wht_deducted', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15)),
                ('notes', models.TextField(blank=True, null=True)),
                ('submission', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tb_securities',
                    to='tax_forms.taxsubmission',
                )),
            ],
            options={
                'db_table': 'tb_securities_income',
            },
        ),
        migrations.AddField(
            model_name='disposalofasset',
            name='category',
            field=models.CharField(
                choices=[
                    ('land_building', 'Land / Building'),
                    ('motor_vehicle', 'Motor Vehicle'),
                    ('shares', 'Shares / Securities'),
                    ('other', 'Other'),
                ],
                default='other',
                max_length=20,
            ),
        ),
    ]
