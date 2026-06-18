from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0015_tb_securities_disposal_category'),
    ]

    operations = [
        # Step 1 — remove the old borrower_name and notes columns
        migrations.RemoveField(model_name='loansgiven', name='borrower_name'),
        migrations.RemoveField(model_name='loansgiven', name='notes'),

        # Step 2 — add the new aggregate fields
        migrations.AddField(
            model_name='loansgiven',
            name='opening_balance',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15),
        ),
        migrations.AddField(
            model_name='loansgiven',
            name='given_during_year',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15),
        ),
        migrations.AddField(
            model_name='loansgiven',
            name='cash_received_from_debtors',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15),
        ),

        # Step 3 — convert ForeignKey → OneToOneField (unique constraint on submission)
        migrations.AlterField(
            model_name='loansgiven',
            name='submission',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='loans_given',
                to='tax_forms.taxsubmission',
            ),
        ),
    ]
