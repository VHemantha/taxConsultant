"""
Management command to encrypt personal data that was stored before field-level
encryption was introduced. Run this once after applying the schema migrations.

Usage:
    python manage.py encrypt_existing_data
    python manage.py encrypt_existing_data --dry-run   (preview counts, no saves)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Encrypt existing plaintext personal data in the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Count affected rows without writing any changes.',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        verb = self.style.WARNING('DRY RUN — ') if dry else ''

        self.stdout.write(f'{verb}Encrypting existing personal data...\n')
        total = 0

        total += self._process('authentication', 'CustomUser',       ['phone'],                                    dry)
        total += self._process('clients',        'ClientProfile',    ['full_name', 'tin', 'pin', 'nic_passport',
                                                                       'telephone', 'mobile', 'address'],          dry)
        total += self._process('tax_forms',      'LocalEmploymentIncome', ['employer_name'],                       dry)
        total += self._process('tax_forms',      'SoleProprietorshipIncome', ['business_name'],                   dry)
        total += self._process('tax_forms',      'ImmovableProperty', ['situation_of_property'],                  dry)
        total += self._process('tax_forms',      'MotorVehicle',      ['registration_no'],                        dry)
        total += self._process('tax_forms',      'BankBalance',       ['bank_name', 'account_no'],                dry)
        total += self._process('tax_forms',      'LoansGiven',        ['borrower_name'],                          dry)
        total += self._process('tax_forms',      'BusinessProperty',  ['name_of_business'],                       dry)
        total += self._process('tax_forms',      'DeclarantDetails',  ['full_name', 'telephone', 'mobile',
                                                                        'email', 'nic_passport', 'tin', 'pin'],   dry)
        total += self._process('tax_forms',      'CashFlowStatement', ['opening_favourable_banks',
                                                                        'opening_overdraft_banks',
                                                                        'closing_favourable_banks',
                                                                        'closing_overdraft_banks'],               dry)

        status = self.style.SUCCESS('Done') if not dry else self.style.WARNING('Dry run complete')
        self.stdout.write(f'\n{status} — {total} rows processed.\n')
        if dry:
            self.stdout.write('Run without --dry-run to apply encryption.\n')

    def _process(self, app_label, model_name, fields, dry):
        from django.apps import apps
        Model = apps.get_model(app_label, model_name)
        qs = Model.objects.all()
        count = qs.count()
        self.stdout.write(f'  {app_label}.{model_name}: {count} rows …', ending='')

        if not dry:
            # Loading the queryset triggers from_db_value (decrypt attempt — falls back
            # for plaintext). Saving re-encrypts via get_prep_value.
            updated = 0
            for obj in qs.iterator(chunk_size=500):
                try:
                    obj.save(update_fields=fields)
                    updated += 1
                except Exception as exc:
                    self.stderr.write(f'\n    ERROR on {model_name} pk={obj.pk}: {exc}')
            self.stdout.write(self.style.SUCCESS(f' {updated} saved.'))
        else:
            self.stdout.write(self.style.WARNING(' (skipped)'))

        return count
