from django.contrib import admin
from .models import (
    TaxYear, TaxSubmission, LocalEmploymentIncome, ForeignIncome,
    TerminalBenefit, RentIncome, InterestIncome, DividendIncome,
    QualifyingPayments, TaxCredits, DeclarantDetails,
)


@admin.register(TaxYear)
class TaxYearAdmin(admin.ModelAdmin):
    list_display = ['label', 'year', 'assessment_year_start', 'assessment_year_end', 'is_active']
    list_filter = ['is_active']


@admin.register(TaxSubmission)
class TaxSubmissionAdmin(admin.ModelAdmin):
    list_display = ['client', 'tax_year', 'status', 'net_tax_payable', 'submitted_at', 'confirmed_at']
    list_filter = ['status', 'tax_year']
    search_fields = ['client__email']
    ordering = ['-created_at']
    readonly_fields = ['total_assessable_income', 'gross_tax', 'net_tax_payable']
