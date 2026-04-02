from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class TaxYear(models.Model):
    year = models.IntegerField(unique=True)
    label = models.CharField(max_length=50)  # e.g., "Y/A 2025/2026"
    assessment_year_start = models.DateField()
    assessment_year_end = models.DateField()
    personal_relief = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1800000.00'))
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'tax_years'
        ordering = ['-year']

    def __str__(self):
        return self.label


class TaxSubmission(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('info_requested', 'Information Requested'),
        ('under_review', 'Under Consultant Review'),
        ('calculation_done', 'Calculation Done'),
        ('awaiting_confirmation', 'Awaiting Client Confirmation'),
        ('confirmed', 'Client Confirmed'),
        ('archived', 'Archived'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tax_submissions'
    )
    tax_year = models.ForeignKey(TaxYear, on_delete=models.PROTECT, related_name='submissions')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    # Consultant fields
    consultant_notes = models.TextField(blank=True, null=True)
    info_request_message = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_submissions'
    )

    # Calculated tax fields (set by consultant/system)
    total_assessable_income = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_qualifying_payments = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    personal_relief = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1800000.00'))
    rent_relief = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_taxable_income = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    gross_tax = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_tax_credits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_tax_payable = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tax_submissions'
        unique_together = ['client', 'tax_year']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client.email} - {self.tax_year.label} ({self.status})"


# ─── INCOME SECTION ──────────────────────────────────────────────────────────

class LocalEmploymentIncome(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='local_employment')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'local_employment_income'


class ForeignIncome(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='foreign_income')
    employment_service_fee = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    other_foreign_income = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'foreign_income'

    @property
    def total(self):
        return self.employment_service_fee + self.other_foreign_income


class TerminalBenefit(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='terminal_benefit')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    benefit_types = models.CharField(max_length=200, blank=True, null=True, help_text='e.g., EPF, ETF, Pension, Gratuity')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'terminal_benefit'


class RentIncome(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='rent_income')
    gross_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    wht_deducted = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'rent_income'


class InterestIncome(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='interest_income')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    wht_deducted = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'interest_income'


class DividendIncome(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='dividend_income')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'dividend_income'


class SoleProprietorshipIncome(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='sole_proprietorship')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    business_name = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sole_proprietorship_income'


class OtherIncome(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='other_income')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'other_income'


# ─── QUALIFYING PAYMENTS ─────────────────────────────────────────────────────

class QualifyingPayments(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='qualifying_payments')
    donation_charitable = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    donation_government = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    solar_panels_expenditure = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)

    SOLAR_MAX = Decimal('600000.00')

    class Meta:
        db_table = 'qualifying_payments'

    @property
    def solar_allowed(self):
        return min(self.solar_panels_expenditure, self.SOLAR_MAX)

    @property
    def total(self):
        return self.donation_charitable + self.donation_government + self.solar_allowed


class SelfAssessmentPayment(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='self_assessment_payments')
    installment_number = models.IntegerField(choices=[(1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th')])
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'self_assessment_payments'
        unique_together = ['submission', 'installment_number']


class TaxCredits(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='tax_credits')
    apit_on_salary = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    wht_rent_interest_service = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    partnership_tax_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'tax_credits'


# ─── ASSETS ──────────────────────────────────────────────────────────────────

class ImmovableProperty(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='immovable_properties')
    situation_of_property = models.CharField(max_length=500, blank=True)
    date_of_acquisition = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    market_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'immovable_properties'
        ordering = ['order']


class MotorVehicle(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='motor_vehicles')
    description = models.CharField(max_length=200, blank=True)
    registration_no = models.CharField(max_length=50, blank=True)
    date_of_acquisition = models.DateField(null=True, blank=True)
    cost_market_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'motor_vehicles'
        ordering = ['order']


class BankBalance(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='bank_balances')
    bank_name = models.CharField(max_length=200, blank=True)
    account_no = models.CharField(max_length=100, blank=True)
    amount_invested = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    interest = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'bank_balances'
        ordering = ['order']


class SharesStocks(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='shares_stocks')
    description = models.CharField(max_length=200, blank=True)
    no_of_shares = models.IntegerField(default=0)
    date_of_acquisition = models.DateField(null=True, blank=True)
    cost_market_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_dividend_income = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'shares_stocks'
        ordering = ['order']


class CashInHand(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='cash_in_hand')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'cash_in_hand'


class LoansGiven(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='loans_given')
    borrower_name = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'loans_given'


class GoldSilverJewellery(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='gold_jewellery')
    description = models.TextField(blank=True, null=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'gold_silver_jewellery'


class BusinessProperty(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='business_properties')
    name_of_business = models.CharField(max_length=200, blank=True)
    current_account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    capital_account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'business_properties'
        ordering = ['order']


class OtherAsset(models.Model):
    ACQUISITION_TYPE = [
        ('purchase', 'Purchase'),
        ('gift', 'Gift'),
        ('exchange', 'Exchange'),
    ]
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='other_assets')
    description = models.CharField(max_length=300, blank=True)
    acquisition_type = models.CharField(max_length=20, choices=ACQUISITION_TYPE, default='purchase')
    date_of_acquisition = models.DateField(null=True, blank=True)
    cost_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'other_assets'
        ordering = ['order']


class DisposalOfAsset(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='disposals')
    description = models.CharField(max_length=300, blank=True)
    date_of_disposal = models.DateField(null=True, blank=True)
    sales_proceed = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    date_acquired = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'disposal_of_assets'
        ordering = ['order']


# ─── LIABILITIES ─────────────────────────────────────────────────────────────

class Liability(models.Model):
    submission = models.ForeignKey(TaxSubmission, on_delete=models.CASCADE, related_name='liabilities')
    description = models.CharField(max_length=300, blank=True)
    security_on_liability = models.CharField(max_length=300, blank=True, null=True)
    date_of_commencement = models.DateField(null=True, blank=True)
    original_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    amount_as_at_date = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    amount_repaid_during_year = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'liabilities'
        ordering = ['order']


# ─── DECLARANT DETAILS ───────────────────────────────────────────────────────

class DeclarantDetails(models.Model):
    submission = models.OneToOneField(TaxSubmission, on_delete=models.CASCADE, related_name='declarant_details')
    full_name = models.CharField(max_length=200)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    nic_passport = models.CharField(max_length=50)
    tin = models.CharField(max_length=50, blank=True, null=True)
    pin = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'declarant_details'


# ─── AUDIT / EDIT LOG ────────────────────────────────────────────────────────

class SubmissionEditLog(models.Model):
    ACTION_CHOICES = [
        ('update', 'Updated'),
        ('add', 'Added Row'),
        ('delete', 'Deleted Row'),
    ]

    submission = models.ForeignKey(
        TaxSubmission, on_delete=models.CASCADE, related_name='edit_logs'
    )
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='form_edits',
    )
    section = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='update')
    description = models.TextField(blank=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'submission_edit_logs'
        ordering = ['-edited_at']

    def __str__(self):
        return f"{self.edited_by} — {self.section} ({self.action})"
