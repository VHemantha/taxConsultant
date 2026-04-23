"""
PDF Generator for Tax Submission Documents
Generates professional tax summary PDFs using ReportLab.

Changes implemented:
  Change 6:  Qualifying payments and tax credits fully included.
  Change 10: Assets & Liabilities statement appended when generating shared doc.
  Change 12: Company name and logo pulled from SystemSettings (singleton).
  Change 16: Exempt dividend income shown in a dedicated section.
  Change 19: Slab breakdown table included in Tax Computation section.
  Change 20: Tax credits section rendered before Balance Tax Payable line.
"""
import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether, Image,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.conf import settings


# ── Brand Colours ─────────────────────────────────────────────────────────────
BLACK = colors.HexColor('#0a0a0a')
YELLOW = colors.HexColor('#F5C518')
RED = colors.HexColor('#DC2626')
WHITE = colors.white
LIGHT_GRAY = colors.HexColor('#F5F5F5')
DARK_GRAY = colors.HexColor('#374151')
PALE_YELLOW = colors.HexColor('#FEF3C7')
PALE_GREEN = colors.HexColor('#D1FAE5')


def fmt_currency(value):
    """Format a decimal value as Sri Lankan Rupees (2 decimal places)."""
    if value is None:
        return 'Rs. 0.00'
    try:
        return f'Rs. {float(value):,.2f}'
    except (TypeError, ValueError):
        return 'Rs. 0.00'


def fmt_number(value):
    """Format a number with comma separators, no decimals."""
    if value is None:
        return '0'
    try:
        return f'{int(float(value)):,}'
    except (TypeError, ValueError):
        return '0'


def _get_system_settings():
    """Safely fetch singleton SystemSettings; return defaults if table missing."""
    try:
        from .models import SystemSettings
        return SystemSettings.get()
    except Exception:
        return None


def _build_styles():
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'Header', parent=styles['Normal'],
        fontSize=18, fontName='Helvetica-Bold',
        textColor=BLACK, alignment=TA_CENTER, spaceAfter=4,
    )
    sub_header_style = ParagraphStyle(
        'SubHeader', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica',
        textColor=DARK_GRAY, alignment=TA_CENTER, spaceAfter=2,
    )
    section_title_style = ParagraphStyle(
        'SectionTitle', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold',
        textColor=WHITE, backColor=BLACK,
        alignment=TA_LEFT, spaceAfter=4, spaceBefore=8,
        leftIndent=6, rightIndent=6, borderPad=4,
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica', textColor=DARK_GRAY,
    )
    value_style = ParagraphStyle(
        'Value', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold',
        textColor=BLACK, alignment=TA_RIGHT,
    )
    note_style = ParagraphStyle(
        'Note', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica', textColor=DARK_GRAY,
        alignment=TA_CENTER, spaceAfter=2,
    )
    return {
        'header': header_style,
        'sub_header': sub_header_style,
        'section_title': section_title_style,
        'label': label_style,
        'value': value_style,
        'note': note_style,
    }


def generate_tax_submission_pdf(submission, include_assets_liabilities=False) -> BytesIO:
    """
    Generate a comprehensive tax submission PDF.

    Args:
        submission: TaxSubmission instance.
        include_assets_liabilities: If True, appends A&L statement (Change 10).

    Returns a BytesIO object containing the PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"DPR-TMS | Tax Return - {submission.tax_year.label}",
    )

    st = _build_styles()
    sys_settings = _get_system_settings()
    elements = []

    # ── Company Header (Change 12) ────────────────────────────────────────────
    company_name = sys_settings.company_name if sys_settings else 'DPR-TMS'
    company_tagline = sys_settings.company_tagline if sys_settings else 'DPR Tax Management System | PERSONAL INCOME TAX RETURN'
    footer_text = sys_settings.footer_text if sys_settings else 'DPR-TMS | Confidential'

    # Logo (if uploaded)
    if sys_settings and sys_settings.company_logo:
        try:
            logo_path = sys_settings.company_logo.path
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=3 * cm, height=1.5 * cm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 4))
        except Exception:
            pass  # logo not available; fall back to text

    elements.append(Paragraph(company_name, st['header']))
    elements.append(Paragraph(company_tagline, st['sub_header']))
    elements.append(Paragraph(f"Year of Assessment: {submission.tax_year.label}", st['sub_header']))
    elements.append(HRFlowable(width="100%", thickness=3, color=YELLOW, spaceAfter=8))

    # ── Declarant Details ─────────────────────────────────────────────────────
    elements.append(Paragraph("DECLARANT DETAILS", st['section_title']))
    dd = getattr(submission, 'declarant_details', None)
    if dd:
        declarant_data = [
            ['Full Name:', dd.full_name, 'TIN:', dd.tin or 'N/A'],
            ['NIC/Passport:', dd.nic_passport, 'PIN:', dd.pin or 'N/A'],
            ['Email:', dd.email, 'Mobile:', dd.mobile or 'N/A'],
            ['Telephone:', dd.telephone or 'N/A', '', ''],
        ]
        t = Table(declarant_data, colWidths=[3 * cm, 7 * cm, 3 * cm, 5 * cm])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), DARK_GRAY),
            ('TEXTCOLOR', (2, 0), (2, -1), DARK_GRAY),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT_GRAY, WHITE]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
    elements.append(Spacer(1, 10))

    # ── Income & Receipts ─────────────────────────────────────────────────────
    elements.append(Paragraph("INCOME & RECEIPTS", st['section_title']))

    income_data = [['Income Source', 'Amount (Rs.)']]

    lei = getattr(submission, 'local_employment', None)
    if lei and lei.amount:
        income_data.append(['Local Employment Income', fmt_currency(lei.amount)])

    fi = getattr(submission, 'foreign_income', None)
    if fi:
        if fi.employment_service_fee:
            income_data.append(['Foreign Employment Income / Service Fee', fmt_currency(fi.employment_service_fee)])
        if fi.other_foreign_income:
            income_data.append(['Other Foreign Source Income', fmt_currency(fi.other_foreign_income)])
        if fi.source_country:
            income_data.append([f'  Source Country: {fi.source_country}', ''])

    tb = getattr(submission, 'terminal_benefit', None)
    if tb and tb.amount:
        income_data.append(['Terminal Benefit', fmt_currency(tb.amount)])

    ri = getattr(submission, 'rent_income', None)
    if ri and ri.gross_amount:
        income_data.append(['Rent Income (Gross)', fmt_currency(ri.gross_amount)])

    ii = getattr(submission, 'interest_income', None)
    if ii and ii.amount:
        income_data.append(['Interest Income', fmt_currency(ii.amount)])

    di = getattr(submission, 'dividend_income', None)
    if di and di.amount:
        income_data.append(['Dividend Income (Taxable)', fmt_currency(di.amount)])

    spi = getattr(submission, 'sole_proprietorship', None)
    if spi and spi.amount:
        income_data.append(['Income from Sole Proprietorship/Partnership', fmt_currency(spi.amount)])

    oi = getattr(submission, 'other_income', None)
    if oi and oi.amount:
        income_data.append(['Other Income', fmt_currency(oi.amount)])

    income_data.append(['TOTAL ASSESSABLE INCOME', fmt_currency(submission.total_assessable_income)])
    _render_two_col_table(elements, income_data, highlight_last=True)

    # ── Exempt Income (Change 16) ─────────────────────────────────────────────
    # Use confirmed value from TaxSubmission; fall back to live DividendIncome.exempt_amount
    # so the PDF is correct even before calculation is confirmed.
    exempt_div = getattr(submission, 'exempt_dividend_income', None) or Decimal('0.00')
    if float(exempt_div) == 0 and di:
        exempt_div = di.exempt_amount or Decimal('0.00')
    if float(exempt_div) > 0:
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("EXEMPT INCOME", st['section_title']))
        exempt_data = [
            ['Description', 'Amount (Rs.)'],
            ['Dividend income exempt (15% WHT — resident companies)', fmt_currency(exempt_div)],
            ['TOTAL EXEMPT INCOME', fmt_currency(exempt_div)],
        ]
        _render_two_col_table(elements, exempt_data, highlight_last=True)

    elements.append(Spacer(1, 8))

    # ── Qualifying Payments & Reliefs (Change 6) ──────────────────────────────
    elements.append(Paragraph("QUALIFYING PAYMENTS AND RELIEFS", st['section_title']))
    qp_data = [['Description', 'Amount (Rs.)']]
    qp = getattr(submission, 'qualifying_payments', None)
    if qp:
        if qp.donation_charitable > 0:
            qp_data.append(['Donation to Approved Charitable Institute', fmt_currency(qp.donation_charitable)])
        if qp.donation_government > 0:
            qp_data.append(['Donation to Government of Sri Lanka', fmt_currency(qp.donation_government)])
        if qp.solar_panels_expenditure > 0:
            qp_data.append([
                'Solar Panels Expenditure (Max Rs. 600,000)',
                fmt_currency(min(qp.solar_panels_expenditure, Decimal('600000'))),
            ])
    qp_data.append(['Personal Relief', fmt_currency(submission.personal_relief)])
    qp_data.append(['Rent Relief (25% of Gross Rent) — auto-calculated', fmt_currency(submission.rent_relief)])
    total_relief = (submission.total_qualifying_payments or Decimal('0')) + (submission.personal_relief or Decimal('0')) + (submission.rent_relief or Decimal('0'))
    qp_data.append(['TOTAL QUALIFYING PAYMENTS & RELIEFS', fmt_currency(total_relief)])
    _render_two_col_table(elements, qp_data, highlight_last=True)
    elements.append(Spacer(1, 8))

    # ── Tax Computation (Change 19 — slab breakdown) ──────────────────────────
    elements.append(Paragraph("TAX COMPUTATION", st['section_title']))

    tax_data = [
        ['', ''],
        ['Total Assessable Income', fmt_currency(submission.total_assessable_income)],
        ['Less: Qualifying Payments', f'({fmt_currency(submission.total_qualifying_payments)})'],
        ['Less: Personal Relief', f'({fmt_currency(submission.personal_relief)})'],
        ['Less: Rent Relief (25% of Gross Rent)', f'({fmt_currency(submission.rent_relief)})'],
        ['TAXABLE INCOME', fmt_currency(submission.net_taxable_income)],
        ['', ''],
    ]

    # Slab breakdown rows
    slab_breakdown = submission.slab_breakdown or []
    if slab_breakdown:
        tax_data.append(['TAX ON TAXABLE INCOME (SLAB BREAKDOWN)', ''])
        for slab in slab_breakdown:
            rate_pct = f"{float(slab['rate']) * 100:.0f}%"
            label = slab.get('label', '')
            tax_data.append([
                f"  {label}",
                fmt_currency(Decimal(slab['tax'])),
            ])
    tax_data.append(['Gross Tax on Taxable Income', fmt_currency(submission.gross_tax)])

    t = Table(tax_data, colWidths=[12 * cm, 6 * cm])
    style = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),  # TAXABLE INCOME row
        ('BACKGROUND', (0, 5), (-1, 5), PALE_YELLOW),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Gross Tax row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E0E7FF')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]
    # Italics for slab rows (index 8 onwards if breakdown exists)
    if slab_breakdown:
        slab_start = 8
        for i in range(len(slab_breakdown)):
            style.append(('FONTNAME', (0, slab_start + i), (0, slab_start + i), 'Helvetica-Oblique'))
            style.append(('TEXTCOLOR', (0, slab_start + i), (0, slab_start + i), DARK_GRAY))
    t.setStyle(TableStyle(style))
    elements.append(t)
    elements.append(Spacer(1, 8))

    # ── Tax Credits (Change 20 — before Balance Tax Payable) ─────────────────
    elements.append(Paragraph("TAX CREDITS", st['section_title']))
    tc = getattr(submission, 'tax_credits', None)
    tc_data = [['Description', 'Amount (Rs.)']]

    if tc:
        if tc.apit_on_salary > 0:
            tc_data.append(['APIT on Salary (T10 Certificate)', fmt_currency(tc.apit_on_salary)])
        if tc.wht_rent_interest_service > 0:
            tc_data.append(['WHT on Rent/Interest/Service Fees', fmt_currency(tc.wht_rent_interest_service)])
        if tc.partnership_tax_credit > 0:
            tc_data.append(['Partnership Tax Credit', fmt_currency(tc.partnership_tax_credit)])

    # WHT Certificates breakdown
    for wht_cert in submission.wht_certificates.all():
        tc_data.append([
            f'WHT Certificate — {wht_cert.get_category_display()}',
            fmt_currency(wht_cert.amount),
        ])

    for sap in submission.self_assessment_payments.all():
        tc_data.append([f'Self Assessment Payment (Installment {sap.installment_number})', fmt_currency(sap.amount)])

    tc_data.append(['TOTAL TAX CREDITS', fmt_currency(submission.total_tax_credits)])
    _render_two_col_table(elements, tc_data, highlight_last=True)
    elements.append(Spacer(1, 6))

    # Balance Tax Payable — individual credit descriptions shown above the payable line
    balance_data = [
        ['Gross Tax on Taxable Income', fmt_currency(submission.gross_tax)],
    ]

    # Individual tax credit lines
    tc_bal = getattr(submission, 'tax_credits', None)
    if tc_bal:
        if (tc_bal.apit_on_salary or Decimal('0')) > 0:
            balance_data.append(['  Less: APIT on Salary (T10 Certificate)', f'({fmt_currency(tc_bal.apit_on_salary)})'])
        if (tc_bal.wht_rent_interest_service or Decimal('0')) > 0:
            balance_data.append(['  Less: WHT on Rent / Interest / Service Fees', f'({fmt_currency(tc_bal.wht_rent_interest_service)})'])
        if (tc_bal.partnership_tax_credit or Decimal('0')) > 0:
            balance_data.append(['  Less: Partnership Tax Credit', f'({fmt_currency(tc_bal.partnership_tax_credit)})'])

    for sap in submission.self_assessment_payments.all():
        balance_data.append([f'  Less: Self Assessment Payment (Installment {sap.installment_number})', f'({fmt_currency(sap.amount)})'])

    total_credits_row = len(balance_data)
    balance_data.append(['Less: Total Tax Credits', f'({fmt_currency(submission.total_tax_credits)})'])

    # Foreign income tax at flat 15% — shown separately above balance
    foreign_income_tax = submission.foreign_income_tax or Decimal('0')
    fi_bal = getattr(submission, 'foreign_income', None)
    net_foreign_row = None
    if fi_bal:
        fi_amount = (fi_bal.employment_service_fee or Decimal('0')) + (fi_bal.other_foreign_income or Decimal('0'))
        fi_paid = fi_bal.foreign_tax_paid or Decimal('0')
        if fi_amount > 0:
            balance_data.append([f'  Add: Foreign Income Tax @ 15% (on Rs. {fmt_currency(fi_amount)})', fmt_currency(fi_amount * Decimal("0.15"))])
            if fi_paid > 0:
                balance_data.append([f'  Less: Foreign Tax Paid (Credit)', f'({fmt_currency(fi_paid)})'])
            net_foreign_row = len(balance_data)
            balance_data.append(['Net Foreign Income Tax Payable', fmt_currency(foreign_income_tax)])

    last_row = len(balance_data)
    balance_data.append(['BALANCE TAX PAYABLE', fmt_currency(submission.net_tax_payable)])

    btp_style = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, last_row), (-1, last_row), 'Helvetica-Bold'),
        ('FONTSIZE', (0, last_row), (-1, last_row), 12),
        ('BACKGROUND', (0, last_row), (-1, last_row), YELLOW),
        ('FONTNAME', (0, total_credits_row), (-1, total_credits_row), 'Helvetica-Bold'),
        ('BACKGROUND', (0, total_credits_row), (-1, total_credits_row), colors.HexColor('#E0E7FF')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 7),
    ]
    if net_foreign_row is not None:
        btp_style.append(('FONTNAME', (0, net_foreign_row), (-1, net_foreign_row), 'Helvetica-Bold'))
        btp_style.append(('BACKGROUND', (0, net_foreign_row), (-1, net_foreign_row), colors.HexColor('#FFF3CD')))
    # Grey out individual detail rows
    for i in range(1, last_row):
        if i not in (total_credits_row, net_foreign_row):
            btp_style.append(('TEXTCOLOR', (0, i), (0, i), DARK_GRAY))
            btp_style.append(('FONTSIZE', (0, i), (-1, i), 9))

    t = Table(balance_data, colWidths=[12 * cm, 6 * cm])
    t.setStyle(TableStyle(btp_style))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # ── Assets & Liabilities (Change 10 — included when sharing) ─────────────
    if include_assets_liabilities:
        _append_assets_liabilities(elements, submission, st)

    # ── Footer ────────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=2, color=YELLOW, spaceAfter=6))
    footer_style = _build_styles()['note']
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y %H:%M')} | {footer_text}",
        footer_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _append_assets_liabilities(elements, submission, st):
    """Append Assets & Liabilities statement to PDF (Change 10)."""
    elements.append(Paragraph("STATEMENT OF ASSETS AND LIABILITIES", st['section_title']))

    # Immovable Properties
    props = submission.immovable_properties.all()
    if props.exists():
        elements.append(Paragraph("Immovable Properties", _italic_style()))
        prop_data = [['Property', 'Date Acquired', 'Cost (Rs.)', 'Market Value (Rs.)']]
        for p in props:
            prop_data.append([
                p.situation_of_property or '—',
                str(p.date_of_acquisition) if p.date_of_acquisition else '—',
                fmt_currency(p.cost),
                fmt_currency(p.market_value),
            ])
        _render_wide_table(elements, prop_data)

    # Motor Vehicles
    vehicles = submission.motor_vehicles.all()
    if vehicles.exists():
        elements.append(Paragraph("Motor Vehicles", _italic_style()))
        v_data = [['Description', 'Reg. No.', 'Date Acquired', 'Value (Rs.)']]
        for v in vehicles:
            v_data.append([
                v.description or '—', v.registration_no or '—',
                str(v.date_of_acquisition) if v.date_of_acquisition else '—',
                fmt_currency(v.cost_market_value),
            ])
        _render_wide_table(elements, v_data)

    # Bank Balances
    banks = submission.bank_balances.all()
    if banks.exists():
        elements.append(Paragraph("Bank Balances", _italic_style()))
        b_data = [['Bank', 'Account No.', 'Invested (Rs.)', 'Interest (Rs.)', 'Balance (Rs.)']]
        for b in banks:
            b_data.append([
                b.bank_name or '—', b.account_no or '—',
                fmt_currency(b.amount_invested), fmt_currency(b.interest), fmt_currency(b.balance),
            ])
        _render_wide_table(elements, b_data, col_count=5)

    # Shares & Stocks
    shares = submission.shares_stocks.all()
    if shares.exists():
        elements.append(Paragraph("Shares & Stocks", _italic_style()))
        s_data = [['Description', 'Shares', 'Value (Rs.)', 'Dividend (Rs.)']]
        for s in shares:
            s_data.append([
                s.description or '—', fmt_number(s.no_of_shares),
                fmt_currency(s.cost_market_value), fmt_currency(s.net_dividend_income),
            ])
        _render_wide_table(elements, s_data)

    # Cash in Hand
    cih = getattr(submission, 'cash_in_hand', None)
    if cih and cih.amount:
        elements.append(Paragraph(f"Cash in Hand: {fmt_currency(cih.amount)}", _italic_style()))

    # Gold & Jewellery
    gold = getattr(submission, 'gold_jewellery', None)
    if gold and gold.value:
        elements.append(Paragraph(f"Gold/Silver/Jewellery: {fmt_currency(gold.value)}", _italic_style()))

    # Other Assets
    others = submission.other_assets.all()
    if others.exists():
        elements.append(Paragraph("Other Assets", _italic_style()))
        oa_data = [['Description', 'Type', 'Date Acquired', 'Value (Rs.)']]
        for o in others:
            oa_data.append([
                o.description or '—', o.get_acquisition_type_display(),
                str(o.date_of_acquisition) if o.date_of_acquisition else '—',
                fmt_currency(o.cost_value),
            ])
        _render_wide_table(elements, oa_data)

    # Liabilities
    liabs = submission.liabilities.all()
    if liabs.exists():
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("LIABILITIES", st['section_title']))
        l_data = [['Description', 'Security', 'Original (Rs.)', 'Balance (Rs.)', 'Repaid (Rs.)']]
        for l in liabs:
            l_data.append([
                l.description or '—', l.security_on_liability or '—',
                fmt_currency(l.original_amount), fmt_currency(l.amount_as_at_date),
                fmt_currency(l.amount_repaid_during_year),
            ])
        _render_wide_table(elements, l_data, col_count=5)

    elements.append(Spacer(1, 10))


def _italic_style():
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        'Italic', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold',
        textColor=DARK_GRAY, spaceBefore=6, spaceAfter=2,
    )


def _render_two_col_table(elements, data, highlight_last=False):
    col_widths = [13 * cm, 5 * cm]
    t = Table(data, colWidths=col_widths)
    style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 0), (-1, 0), BLACK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]
    if highlight_last and len(data) > 1:
        style += [
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), YELLOW),
            ('TEXTCOLOR', (0, -1), (-1, -1), BLACK),
        ]
    t.setStyle(TableStyle(style))
    elements.append(t)


def _render_wide_table(elements, data, col_count=4):
    """Render a multi-column asset/liability table."""
    page_width = A4[0] - 3 * cm  # approx usable width
    col_w = page_width / col_count
    col_widths = [col_w] * col_count
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), DARK_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4))
