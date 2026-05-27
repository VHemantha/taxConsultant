from django.db import migrations
import encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0013_sole_proprietorship_multi'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashflowstatement',
            name='receipt_other_items',
            field=encrypted_fields.EncryptedJSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='cashflowstatement',
            name='payment_other_items',
            field=encrypted_fields.EncryptedJSONField(blank=True, default=list),
        ),
    ]
