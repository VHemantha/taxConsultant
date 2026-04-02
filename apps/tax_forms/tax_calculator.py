"""
Sri Lanka Personal Income Tax Calculator - Y/A 2025/2026
Tax slabs per the Inland Revenue Act amendments.
"""
from decimal import Decimal, ROUND_HALF_UP


TAX_SLABS = [
    (Decimal('1200000'), Decimal('0.06')),
    (Decimal('1200000'), Decimal('0.12')),
    (Decimal('1200000'), Decimal('0.18')),
    (Decimal('1200000'), Decimal('0.24')),
    (Decimal('1200000'), Decimal('0.30')),
    (None, Decimal('0.36')),  # Balance
]

PERSONAL_RELIEF = Decimal('1800000.00')
SOLAR_MAX = Decimal('600000.00')


def calculate_tax_on_income(taxable_income: Decimal) -> Decimal:
    """Calculate gross tax based on Sri Lanka tax slabs."""
    if taxable_income <= 0:
        return Decimal('0.00')

    tax = Decimal('0.00')
    remaining = taxable_income

    for slab_amount, rate in TAX_SLABS:
        if remaining <= 0:
            break
        if slab_amount is None:
            tax += remaining * rate
            break
        applicable = min(remaining, slab_amount)
        tax += applicable * rate
        remaining -= applicable

    return tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_full_tax(submission) -> dict:
    """
    Calculate full tax liability for a submission.
    Returns a dict with all calculated values.
    """
    # 1. Total Assessable Income
    local_emp = Decimal('0.00')
    if hasattr(submission, 'local_employment'):
        local_emp = submission.local_employment.amount or Decimal('0.00')

    foreign = Decimal('0.00')
    if hasattr(submission, 'foreign_income'):
        fi = submission.foreign_income
        foreign = (fi.employment_service_fee or Decimal('0.00')) + (fi.other_foreign_income or Decimal('0.00'))

    terminal = Decimal('0.00')
    if hasattr(submission, 'terminal_benefit'):
        terminal = submission.terminal_benefit.amount or Decimal('0.00')

    rent_gross = Decimal('0.00')
    if hasattr(submission, 'rent_income'):
        rent_gross = submission.rent_income.gross_amount or Decimal('0.00')

    interest = Decimal('0.00')
    if hasattr(submission, 'interest_income'):
        interest = submission.interest_income.amount or Decimal('0.00')

    dividend = Decimal('0.00')
    if hasattr(submission, 'dividend_income'):
        dividend = submission.dividend_income.amount or Decimal('0.00')

    sole_prop = Decimal('0.00')
    if hasattr(submission, 'sole_proprietorship'):
        sole_prop = submission.sole_proprietorship.amount or Decimal('0.00')

    other_inc = Decimal('0.00')
    if hasattr(submission, 'other_income'):
        other_inc = submission.other_income.amount or Decimal('0.00')

    total_assessable = (
        local_emp + foreign + terminal + rent_gross +
        interest + dividend + sole_prop + other_inc
    )

    # 2. Qualifying Payments & Reliefs
    donation_charitable = Decimal('0.00')
    donation_govt = Decimal('0.00')
    solar = Decimal('0.00')

    if hasattr(submission, 'qualifying_payments'):
        qp = submission.qualifying_payments
        donation_charitable = qp.donation_charitable or Decimal('0.00')
        donation_govt = qp.donation_government or Decimal('0.00')
        solar = min(qp.solar_panels_expenditure or Decimal('0.00'), SOLAR_MAX)

    total_qualifying = donation_charitable + donation_govt + solar

    # 3. Reliefs
    personal_relief = PERSONAL_RELIEF
    rent_relief = (rent_gross * Decimal('0.25')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    total_reliefs = personal_relief + rent_relief

    # 4. Net Taxable Income
    net_taxable = total_assessable - total_qualifying - total_reliefs
    if net_taxable < 0:
        net_taxable = Decimal('0.00')

    # 5. Gross Tax
    gross_tax = calculate_tax_on_income(net_taxable)

    # 6. Tax Credits
    apit = Decimal('0.00')
    wht = Decimal('0.00')
    partnership_credit = Decimal('0.00')
    self_assessment_total = Decimal('0.00')

    if hasattr(submission, 'tax_credits'):
        tc = submission.tax_credits
        apit = tc.apit_on_salary or Decimal('0.00')
        wht = tc.wht_rent_interest_service or Decimal('0.00')
        partnership_credit = tc.partnership_tax_credit or Decimal('0.00')

    # Self assessment payments
    for sap in submission.self_assessment_payments.all():
        self_assessment_total += sap.amount or Decimal('0.00')

    total_credits = apit + wht + partnership_credit + self_assessment_total

    # 7. Net Tax Payable
    net_tax = gross_tax - total_credits
    if net_tax < 0:
        net_tax = Decimal('0.00')

    return {
        'total_assessable_income': total_assessable,
        'total_qualifying_payments': total_qualifying,
        'personal_relief': personal_relief,
        'rent_relief': rent_relief,
        'net_taxable_income': net_taxable,
        'gross_tax': gross_tax,
        'total_tax_credits': total_credits,
        'net_tax_payable': net_tax,
        # Breakdown for reference
        'breakdown': {
            'local_employment': local_emp,
            'foreign_income': foreign,
            'terminal_benefit': terminal,
            'rent_income': rent_gross,
            'interest_income': interest,
            'dividend_income': dividend,
            'sole_proprietorship': sole_prop,
            'other_income': other_inc,
            'donation_charitable': donation_charitable,
            'donation_government': donation_govt,
            'solar_panels': solar,
            'apit': apit,
            'wht': wht,
            'partnership_credit': partnership_credit,
            'self_assessment': self_assessment_total,
        }
    }
