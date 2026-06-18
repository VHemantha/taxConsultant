from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0016_loans_given_aggregate'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashflowstatement',
            name='receipt_debtor_received',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15),
        ),
    ]
