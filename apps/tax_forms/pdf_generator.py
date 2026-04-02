"""
PDF Generator for Tax Submission Documents
Generates professional tax summary PDFs using ReportLab.
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
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.conf import settings


# Brand Colors
BLACK = colors.HexColor('#0a0a0a')
YELLOW = colors.HexColor('#F5C518')
RED = colors.HexColor('#DC2626')
WHITE = colors.white
LIGHT_GRAY = colors.HexColor('#F5F5F5')
DARK_GRAY = colors.HexColor('#374151')


def fmt_currency(value):
    """Format a decimal value as Sri Lankan Rupees."""
    if value is None:
        return 'Rs. 0.00'
    return f'Rs. {value:,.2f}'


def generate_tax_submission_pdf(submission) -> BytesIO:
    """
    Generate a comprehensive tax submission PDF.
    Returns a BytesIO object containing the PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Tax Submission - {submission.tax_year.label}",
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Header ──────────────────────────────────────────────────────────────
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=BLACK,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    sub_header_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=WHITE,
        backColor=BLACK,
        alignment=TA_LEFT,
        spaceAfter=4,
        spaceBefore=8,
        leftIndent=6,
        rightIndent=6,
        borderPad=4,
    )
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=DARK_GRAY,
    )
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=BLACK,
        alignment=TA_RIGHT,
    )
    bold_value_style = ParagraphStyle(
        'BoldValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=BLACK,
        alignment=TA_RIGHT,
    )

    # Company Header
    elements.append(Paragraph("TAX AUTOMATION PORTAL", header_style))
    elements.append(Paragraph("PERSONAL INCOME TAX RETURN", sub_header_style))
    elements.append(Paragraph(f"Year of Assessment: {submission.tax_year.label}", sub_header_style))
    elements.append(HRFlowable(width="100%", thickness=3, color=YELLOW, spaceAfter=8))

    # Declarant Info
    elements.append(Paragraph("DECLARANT DETAILS", section_title_style))
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

    # ── Income Section ───────────────────────────────────────────────────────
    elements.append(Paragraph("INCOME & RECEIPTS", section_title_style))

    income_data = [['Income Source', 'Amount (Rs.)']]

    lei = getattr(submission, 'local_employment', None)
    if lei:
        income_data.append(['Local Employment Income', fmt_currency(lei.amount)])

    fi = getattr(submission, 'foreign_income', None)
    if fi:
        income_data.append(['Foreign Employment Income / Service Fee', fmt_currency(fi.employment_service_fee)])
        income_data.append(['Other Foreign Source Income', fmt_currency(fi.other_foreign_income)])

    tb = getattr(submission, 'terminal_benefit', None)
    if tb:
        income_data.append(['Terminal Benefit', fmt_currency(tb.amount)])

    ri = getattr(submission, 'rent_income', None)
    if ri:
        income_data.append(['Rent Income (Gross)', fmt_currency(ri.gross_amount)])

    ii = getattr(submission, 'interest_income', None)
    if ii:
        income_data.append(['Interest Income', fmt_currency(ii.amount)])

    di = getattr(submission, 'dividend_income', None)
    if di:
        income_data.append(['Dividend Income', fmt_currency(di.amount)])

    spi = getattr(submission, 'sole_proprietorship', None)
    if spi:
        income_data.append(['Income from Sole Proprietorship/Partnership', fmt_currency(spi.amount)])

    oi = getattr(submission, 'other_income', None)
    if oi:
        income_data.append(['Other Income', fmt_currency(oi.amount)])

    income_data.append(['TOTAL ASSESSABLE INCOME', fmt_currency(submission.total_assessable_income)])

    _render_income_table(elements, income_data, highlight_last=True)

    elements.append(Spacer(1, 8))

    # ── Qualifying Payments ──────────────────────────────────────────────────
    elements.append(Paragraph("QUALIFYING PAYMENTS AND RELIEFS", section_title_style))

    qp_data = [['Description', 'Amount (Rs.)']]
    qp = getattr(submission, 'qualifying_payments', None)
    if qp:
        if qp.donation_charitable > 0:
            qp_data.append(['Donation to Approved Charitable Institute', fmt_currency(qp.donation_charitable)])
        if qp.donation_government > 0:
            qp_data.append(['Donation to Government of Sri Lanka', fmt_currency(qp.donation_government)])
        if qp.solar_panels_expenditure > 0:
            qp_data.append([
                f'Solar Panels Expenditure (Max Rs. 600,000)',
                fmt_currency(min(qp.solar_panels_expenditure, Decimal('600000')))
            ])

    qp_data.append(['Personal Relief', fmt_currency(submission.personal_relief)])
    qp_data.append(['Rent Relief (25% of Gross Rent)', fmt_currency(submission.rent_relief)])
    qp_data.append(['TOTAL QUALIFYING PAYMENTS & RELIEFS',
                     fmt_currency(submission.total_qualifying_payments + submission.personal_relief + submission.rent_relief)])

    _render_income_table(elements, qp_data, highlight_last=True)
    elements.append(Spacer(1, 8))

    # ── Tax Computation ──────────────────────────────────────────────────────
    elements.append(Paragraph("TAX COMPUTATION", section_title_style))

    tax_data = [
        ['', ''],
        ['Total Assessable Income', fmt_currency(submission.total_assessable_income)],
        ['Less: Qualifying Payments', f'({fmt_currency(submission.total_qualifying_payments)})'],
        ['Less: Personal Relief', f'({fmt_currency(submission.personal_relief)})'],
        ['Less: Rent Relief', f'({fmt_currency(submission.rent_relief)})'],
        ['NET TAXABLE INCOME', fmt_currency(submission.net_taxable_income)],
        ['', ''],
        ['Gross Tax on Taxable Income', fmt_currency(submission.gross_tax)],
        ['Less: Total Tax Credits', f'({fmt_currency(submission.total_tax_credits)})'],
        ['NET TAX PAYABLE', fmt_currency(submission.net_tax_payable)],
    ]

    t = Table(tax_data, colWidths=[12 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTNAME', (0, 9), (-1, 9), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 9), (-1, 9), 11),
        ('BACKGROUND', (0, 9), (-1, 9), YELLOW),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#FEF3C7')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)

    elements.append(Spacer(1, 12))

    # ── Tax Credits Breakdown ────────────────────────────────────────────────
    elements.append(Paragraph("TAX CREDITS", section_title_style))
    tc = getattr(submission, 'tax_credits', None)
    tc_data = [['Description', 'Amount (Rs.)']]

    if tc:
        if tc.apit_on_salary > 0:
            tc_data.append(['APIT on Salary (T10 Certificate)', fmt_currency(tc.apit_on_salary)])
        if tc.wht_rent_interest_service > 0:
            tc_data.append(['WHT on Rent/Interest/Service Fees', fmt_currency(tc.wht_rent_interest_service)])
        if tc.partnership_tax_credit > 0:
            tc_data.append(['Partnership Tax Credit', fmt_currency(tc.partnership_tax_credit)])

    for sap in submission.self_assessment_payments.all():
        tc_data.append([f'Self Assessment Payment (Installment {sap.installment_number})', fmt_currency(sap.amount)])

    tc_data.append(['TOTAL TAX CREDITS', fmt_currency(submission.total_tax_credits)])
    _render_income_table(elements, tc_data, highlight_last=True)

    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=2, color=YELLOW, spaceAfter=6))

    # Footer
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=DARK_GRAY, alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y %H:%M')} | Tax Automation Portal | Confidential",
        footer_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _render_income_table(elements, data, highlight_last=False):
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
