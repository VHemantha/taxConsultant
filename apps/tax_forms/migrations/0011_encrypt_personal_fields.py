from django.db import migrations
import encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('tax_forms', '0010_foreignincome_foreign_business_income'),
    ]

    operations = [
        # DeclarantDetails — all personal fields
        migrations.AlterField(
            model_name='declarantdetails',
            name='full_name',
            field=encrypted_fields.EncryptedCharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='declarantdetails',
            name='telephone',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='declarantdetails',
            name='mobile',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='declarantdetails',
            name='email',
            field=encrypted_fields.EncryptedCharField(max_length=254),
        ),
        migrations.AlterField(
            model_name='declarantdetails',
            name='nic_passport',
            field=encrypted_fields.EncryptedCharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='declarantdetails',
            name='tin',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='declarantdetails',
            name='pin',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=50, null=True),
        ),
        # LocalEmploymentIncome
        migrations.AlterField(
            model_name='localemploymentincome',
            name='employer_name',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=200, null=True),
        ),
        # SoleProprietorshipIncome
        migrations.AlterField(
            model_name='soleproprietorshipincome',
            name='business_name',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=200, null=True),
        ),
        # ImmovableProperty
        migrations.AlterField(
            model_name='immovableproperty',
            name='situation_of_property',
            field=encrypted_fields.EncryptedCharField(max_length=500),
        ),
        # MotorVehicle
        migrations.AlterField(
            model_name='motorvehicle',
            name='registration_no',
            field=encrypted_fields.EncryptedCharField(max_length=50),
        ),
        # BankBalance
        migrations.AlterField(
            model_name='bankbalance',
            name='bank_name',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='bankbalance',
            name='account_no',
            field=encrypted_fields.EncryptedCharField(max_length=100),
        ),
        # LoansGiven
        migrations.AlterField(
            model_name='loansgiven',
            name='borrower_name',
            field=encrypted_fields.EncryptedCharField(max_length=200),
        ),
        # BusinessProperty
        migrations.AlterField(
            model_name='businessproperty',
            name='name_of_business',
            field=encrypted_fields.EncryptedCharField(blank=True, max_length=200),
        ),
        # CashFlowStatement — bank list fields (JSONField → EncryptedJSONField)
        migrations.AlterField(
            model_name='cashflowstatement',
            name='opening_favourable_banks',
            field=encrypted_fields.EncryptedJSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='cashflowstatement',
            name='opening_overdraft_banks',
            field=encrypted_fields.EncryptedJSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='cashflowstatement',
            name='closing_favourable_banks',
            field=encrypted_fields.EncryptedJSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='cashflowstatement',
            name='closing_overdraft_banks',
            field=encrypted_fields.EncryptedJSONField(blank=True, default=list),
        ),
    ]
