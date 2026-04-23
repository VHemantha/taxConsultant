from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0006_seed_previous_tax_years'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsubmission',
            name='foreign_income_tax',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15),
        ),
    ]
