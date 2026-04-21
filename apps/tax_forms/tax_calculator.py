"""
Sri Lanka Personal Income Tax Calculator - Y/A 2025/2026
Tax slabs per the Inland Revenue Act amendments.
"""
from decimal import Decimal, ROUND_HALF_UP


TAX_SLABS = [
    (Decimal('1000000'), Decimal('0.06')),   # First Rs. 1,000,000 @ 6%
    (Decimal('500000'),  Decimal('0.18')),   # Next Rs. 500,000 @ 18%
    (Decimal('500000'),  Decimal('0.24')),   # Next Rs. 500,000 @ 24%
    (Decimal('500000'),  Decimal('0.30')),   # Next Rs. 500,000 @ 30%
    (None,               Decimal('0.36')),   # Balance @ 36%
]

PERSONAL_RELIEF = Decimal('1800000.00')
SOLAR_MAX = Decimal('600000.00')
RENT_RELIEF_RATE = Decimal('0.25')


def calculate_tax_on_income(taxable_income: Decimal) -> tuple[Decimal, list[dict]]:
    """
    Calculate gross tax based on Sri Lanka tax slabs.
    Returns (gross_tax, slab_breakdown) where slab_breakdown is a list of dicts
    showing each slab's taxable amount and tax computed.
    """
    if taxable_income <= 0:
        return Decimal('0.00'), []

    tax = Decimal('0.00')
    remaining = taxable_income
    slab_breakdown = []
    slab_labels = [
        'First Rs. 1,000,000 @ 6%',
        'Next Rs. 500,000 @ 18%',
        'Next Rs. 500,000 @ 24%',
        'Next Rs. 500,000 @ 30%',
        'Balance @ 36%',
    ]

    for idx, (slab_amount, rate) in enumerate(TAX_SLABS):
        if remaining <= 0:
            break
        if slab_amount is None:
            applicable = remaining
            slab_tax = (applicable * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            tax += slab_tax
            slab_breakdown.append({
                'label': slab_labels[idx],
                'rate': str(rate),
                'taxable_amount': str(applicable.quantize(Decimal('0.01'))),
                'tax': str(slab_tax),
            })
            break
        applicable = min(remaining, slab_amount)
        slab_tax = (applicable * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        tax += slab_tax
        slab_breakdown.append({
            'label': slab_labels[idx],
            'rate': str(rate),
            'taxable_amount': str(applicable.quantize(Decimal('0.01'))),
            'tax': str(slab_tax),
        })
        remaining -= applicable

    return tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), slab_breakdown


def calculate_full_tax(submission) -> dict:
    """
    Calculate full tax liability for a submission.
    Returns a dict with all calculated values and a detailed slab breakdown.

    Change 5: All income sources are now correctly summed.
    Change 16: Exempt dividends (15% WHT from resident companies) are excluded
               from TAI and tracked separately.
    Change 17: Rent relief is auto-calculated at 25% of gross rent.
    Change 18: Foreign income included with foreign_tax_paid as tax credit.
    Change 19: Returns slab_breakdown for detailed display.
    """
    # ── 1. Income sources ────────────────────────────────────────────────────

    local_emp = Decimal('0.00')
    if hasattr(submission, 'local_employment'):
        local_emp = submission.local_employment.amount or Decimal('0.00')

    # Foreign income (Change 18)
    foreign = Decimal('0.00')
    foreign_tax_paid = Decimal('0.00')
    if hasattr(submission, 'foreign_income'):
        fi = submission.foreign_income
        foreign = (fi.employment_service_fee or Decimal('0.00')) + (fi.other_foreign_income or Decimal('0.00'))
        foreign_tax_paid = fi.foreign_tax_paid or Decimal('0.00')

    terminal = Decimal('0.00')
    if hasattr(submission, 'terminal_benefit'):
        terminal = submission.terminal_benefit.amount or Decimal('0.00')

    rent_gross = Decimal('0.00')
    if hasattr(submission, 'rent_income'):
        rent_gross = submission.rent_income.gross_amount or Decimal('0.00')

    interest = Decimal('0.00')
    if hasattr(submission, 'interest_income'):
        interest = submission.interest_income.amount or Decimal('0.00')

    # Dividend income — separate taxable vs exempt (Change 16)
    dividend_taxable = Decimal('0.00')
    dividend_exempt = Decimal('0.00')
    if hasattr(submission, 'dividend_income'):
        di = submission.dividend_income
        dividend_taxable = di.amount or Decimal('0.00')
        dividend_exempt = di.exempt_amount or Decimal('0.00')

    sole_prop = Decimal('0.00')
    if hasattr(submission, 'sole_proprietorship'):
        sole_prop = submission.sole_proprietorship.amount or Decimal('0.00')

    other_inc = Decimal('0.00')
    if hasattr(submission, 'other_income'):
        other_inc = submission.other_income.amount or Decimal('0.00')

    # Total Assessable Income EXCLUDES exempt dividends (Change 16)
    total_assessable = (
        local_emp + foreign + terminal + rent_gross +
        interest + dividend_taxable + sole_prop + other_inc
    )

    # ── 2. Qualifying Payments & Reliefs ────────────────────────────────────

    donation_charitable = Decimal('0.00')
    donation_govt = Decimal('0.00')
    solar = Decimal('0.00')

    if hasattr(submission, 'qualifying_payments'):
        qp = submission.qualifying_payments
        donation_charitable = qp.donation_charitable or Decimal('0.00')
        donation_govt = qp.donation_government or Decimal('0.00')
        solar = min(qp.solar_panels_expenditure or Decimal('0.00'), SOLAR_MAX)

    total_qualifying = donation_charitable + donation_govt + solar

    # Reliefs
    personal_relief = PERSONAL_RELIEF
    # Auto rent relief: 25% of gross rent (Change 17)
    rent_relief = (rent_gross * RENT_RELIEF_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # ── 3. Taxable Income ────────────────────────────────────────────────────

    net_taxable = total_assessable - total_qualifying - personal_relief - rent_relief
    if net_taxable < 0:
        net_taxable = Decimal('0.00')

    # ── 4. Tax Computation with slab breakdown (Change 19) ──────────────────

    gross_tax, slab_breakdown = calculate_tax_on_income(net_taxable)

    # ── 5. Tax Credits ───────────────────────────────────────────────────────

    apit = Decimal('0.00')
    wht = Decimal('0.00')
    partnership_credit = Decimal('0.00')
    self_assessment_total = Decimal('0.00')

    if hasattr(submission, 'tax_credits'):
        tc = submission.tax_credits
        apit = tc.apit_on_salary or Decimal('0.00')
        wht = tc.wht_rent_interest_service or Decimal('0.00')
        partnership_credit = tc.partnership_tax_credit or Decimal('0.00')

    for sap in submission.self_assessment_payments.all():
        self_assessment_total += sap.amount or Decimal('0.00')

    # Foreign tax paid counts as a credit (Change 18)
    total_credits = apit + wht + partnership_credit + self_assessment_total + foreign_tax_paid

    # ── 6. Net Tax Payable ───────────────────────────────────────────────────

    net_tax = gross_tax - total_credits
    if net_tax < 0:
        net_tax = Decimal('0.00')

    return {
        'total_assessable_income': total_assessable,
        'exempt_dividend_income': dividend_exempt,   # Change 16
        'total_qualifying_payments': total_qualifying,
        'personal_relief': personal_relief,
        'rent_relief': rent_relief,                  # Change 17: auto-calculated
        'net_taxable_income': net_taxable,
        'gross_tax': gross_tax,
        'total_tax_credits': total_credits,
        'net_tax_payable': net_tax,
        'slab_breakdown': slab_breakdown,            # Change 19
        # Detailed breakdown for reference / PDF
        'breakdown': {
            'local_employment': local_emp,
            'foreign_income': foreign,
            'foreign_tax_paid': foreign_tax_paid,
            'terminal_benefit': terminal,
            'rent_income': rent_gross,
            'interest_income': interest,
            'dividend_income': dividend_taxable,
            'dividend_exempt': dividend_exempt,
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
