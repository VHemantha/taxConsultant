from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0012_taxsubmission_payment_slip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='soleproprietorshipincome',
            name='submission',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sole_proprietorships',
                to='tax_forms.taxsubmission',
            ),
        ),
        migrations.AddField(
            model_name='soleproprietorshipincome',
            name='wht_deducted',
            field=models.DecimalField(
                blank=True, decimal_places=2, default='0.00', max_digits=15, null=True,
            ),
        ),
    ]
