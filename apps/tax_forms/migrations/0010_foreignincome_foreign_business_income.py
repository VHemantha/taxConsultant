from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0009_cash_flow_statement'),
    ]

    operations = [
        migrations.AddField(
            model_name='foreignincome',
            name='foreign_business_income',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15),
        ),
    ]
