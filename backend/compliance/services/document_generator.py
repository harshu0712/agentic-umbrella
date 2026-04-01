"""
Statutory Document Generator — Module 6

Generates PDF documents: Payslips, P45, P60.
Uses ReportLab for PDF generation.
Documents must be retained for 7 years per UK employment law.
"""

import io
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

from compliance.models import StatutoryDocument
from compliance.constants import DOCUMENT_RETENTION_YEARS
from core.enums import StatutoryDocumentType, AuditEventType
from audit.services import AuditService

logger = logging.getLogger('compliance')


class DocumentGeneratorService:
    """Generates statutory PDF documents — Payslips, P45, P60."""

    @staticmethod
    def generate_payslip(work_record, payroll_data: dict) -> StatutoryDocument:
        """
        Generate a payslip PDF for a completed payroll run.

        Payslip must contain:
        - Gross pay
        - Itemised deductions (tax, NI, fees)
        - Net pay
        - Payment date
        - Tax code used
        - Period covered
        """
        contractor = work_record.contractor
        contractor_link = contractor.contractor_link
        umbrella = work_record.umbrella

        # Determine tax period
        from compliance.services.rti_generator import RTIGeneratorService
        tax_year, tax_period = RTIGeneratorService._get_tax_period(
            work_record.period_end
        )

        # Build payslip data
        financial_data = {
            'employee_name': contractor.get_full_name(),
            'employee_email': contractor.email,
            'ni_number': contractor_link.ni_number if contractor_link else 'N/A',
            'tax_code': contractor_link.tax_code if contractor_link else 'N/A',
            'employer_name': umbrella.name,
            'paye_reference': umbrella.paye_reference,
            'pay_period': f'{work_record.period_start} to {work_record.period_end}',
            'payment_date': str(work_record.period_end),
            'tax_year': tax_year,
            'tax_period': tax_period,
            'hours_worked': str(work_record.hours_worked),
            'hourly_rate': str(work_record.hourly_rate),
            **payroll_data,
        }

        # Generate PDF
        pdf_buffer = DocumentGeneratorService._build_payslip_pdf(financial_data)

        # File name
        file_name = (
            f"payslip_{contractor.last_name}_{work_record.period_start}"
            f"_to_{work_record.period_end}.pdf"
        )

        # Save document record
        doc = StatutoryDocument(
            document_type=StatutoryDocumentType.PAYSLIP,
            contractor=contractor,
            work_record=work_record,
            organisation=umbrella,
            file_name=file_name,
            financial_data=financial_data,
            tax_year=tax_year,
            period_start=work_record.period_start,
            period_end=work_record.period_end,
            retention_until=date.today() + timedelta(
                days=DOCUMENT_RETENTION_YEARS * 365
            ),
        )
        doc.file.save(file_name, ContentFile(pdf_buffer.getvalue()))
        doc.file_size = doc.file.size
        doc.save()

        # Audit log
        AuditService.log(
            event_type=AuditEventType.DOCUMENT_GENERATED,
            work_record=work_record,
            organisation=umbrella,
            metadata={
                'document_id': str(doc.id),
                'document_type': 'PAYSLIP',
                'file_name': file_name,
            },
        )

        logger.info('Payslip generated: %s', file_name)
        return doc

    @staticmethod
    def generate_p45(contractor, leaving_date: date,
                     ytd_data: dict) -> StatutoryDocument:
        """
        Generate a P45 (leaving certificate) when a contractor exits.

        Contains: pay to date, tax deducted to date, tax code, NI number.
        """
        contractor_link = contractor.contractor_link
        umbrella = contractor_link.umbrella

        from compliance.services.rti_generator import RTIGeneratorService
        tax_year, _ = RTIGeneratorService._get_tax_period(leaving_date)

        financial_data = {
            'employee_name': contractor.get_full_name(),
            'ni_number': contractor_link.ni_number,
            'tax_code': contractor_link.tax_code,
            'employer_name': umbrella.name,
            'paye_reference': umbrella.paye_reference,
            'leaving_date': str(leaving_date),
            'tax_year': tax_year,
            **ytd_data,
        }

        pdf_buffer = DocumentGeneratorService._build_p45_pdf(financial_data)

        file_name = f"p45_{contractor.last_name}_{leaving_date}.pdf"

        doc = StatutoryDocument(
            document_type=StatutoryDocumentType.P45,
            contractor=contractor,
            organisation=umbrella,
            file_name=file_name,
            financial_data=financial_data,
            tax_year=tax_year,
            period_end=leaving_date,
            retention_until=date.today() + timedelta(
                days=DOCUMENT_RETENTION_YEARS * 365
            ),
        )
        doc.file.save(file_name, ContentFile(pdf_buffer.getvalue()))
        doc.file_size = doc.file.size
        doc.save()

        AuditService.log(
            event_type=AuditEventType.DOCUMENT_GENERATED,
            organisation=umbrella,
            metadata={
                'document_id': str(doc.id),
                'document_type': 'P45',
                'contractor': contractor.email,
            },
        )

        logger.info('P45 generated for %s', contractor.email)
        return doc

    @staticmethod
    def generate_p60(contractor, tax_year: str,
                     annual_data: dict) -> StatutoryDocument:
        """
        Generate a P60 (annual summary) at end of tax year.

        Contains: total pay, total tax deducted, NI contributions for the year.
        """
        contractor_link = contractor.contractor_link
        umbrella = contractor_link.umbrella

        financial_data = {
            'employee_name': contractor.get_full_name(),
            'ni_number': contractor_link.ni_number,
            'tax_code': contractor_link.tax_code,
            'employer_name': umbrella.name,
            'paye_reference': umbrella.paye_reference,
            'tax_year': tax_year,
            **annual_data,
        }

        pdf_buffer = DocumentGeneratorService._build_p60_pdf(financial_data)

        file_name = f"p60_{contractor.last_name}_{tax_year}.pdf"

        doc = StatutoryDocument(
            document_type=StatutoryDocumentType.P60,
            contractor=contractor,
            organisation=umbrella,
            file_name=file_name,
            financial_data=financial_data,
            tax_year=tax_year,
            retention_until=date.today() + timedelta(
                days=DOCUMENT_RETENTION_YEARS * 365
            ),
        )
        doc.file.save(file_name, ContentFile(pdf_buffer.getvalue()))
        doc.file_size = doc.file.size
        doc.save()

        AuditService.log(
            event_type=AuditEventType.DOCUMENT_GENERATED,
            organisation=umbrella,
            metadata={
                'document_id': str(doc.id),
                'document_type': 'P60',
                'contractor': contractor.email,
                'tax_year': tax_year,
            },
        )

        logger.info('P60 generated for %s, year %s', contractor.email, tax_year)
        return doc

    # ====================================================================
    # PDF BUILDERS
    # ====================================================================

    @staticmethod
    def _build_payslip_pdf(data: dict) -> io.BytesIO:
        """Build a professional payslip PDF using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'PayslipTitle', parent=styles['Heading1'],
            fontSize=18, textColor=colors.HexColor('#1a237e'),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            'PayslipSubtitle', parent=styles['Normal'],
            fontSize=10, textColor=colors.grey,
        )
        section_style = ParagraphStyle(
            'Section', parent=styles['Heading2'],
            fontSize=12, textColor=colors.HexColor('#283593'),
            spaceBefore=12, spaceAfter=6,
        )

        elements = []

        # Header
        elements.append(Paragraph('PAYSLIP', title_style))
        elements.append(Paragraph(
            f"Employer: {data.get('employer_name', 'N/A')} | "
            f"PAYE Ref: {data.get('paye_reference', 'N/A')}",
            subtitle_style
        ))
        elements.append(Spacer(1, 6 * mm))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#1a237e')))
        elements.append(Spacer(1, 4 * mm))

        # Employee details
        elements.append(Paragraph('Employee Details', section_style))
        employee_table = Table([
            ['Name:', data.get('employee_name', 'N/A'), 'NI Number:', data.get('ni_number', 'N/A')],
            ['Tax Code:', data.get('tax_code', 'N/A'), 'Pay Period:', data.get('pay_period', 'N/A')],
            ['Payment Date:', data.get('payment_date', 'N/A'), 'Tax Year:', data.get('tax_year', 'N/A')],
        ], colWidths=[80, 160, 80, 160])
        employee_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(employee_table)
        elements.append(Spacer(1, 4 * mm))

        # Earnings
        elements.append(Paragraph('Earnings', section_style))
        earnings_data = [
            ['Description', 'Hours', 'Rate', 'Amount'],
            [
                'Basic Pay',
                data.get('hours_worked', '0'),
                f"£{data.get('hourly_rate', '0')}",
                f"£{data.get('gross_pay', '0')}",
            ],
        ]
        earnings_table = Table(earnings_data, colWidths=[200, 80, 100, 100])
        earnings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eaf6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(earnings_table)
        elements.append(Spacer(1, 4 * mm))

        # Deductions
        elements.append(Paragraph('Deductions', section_style))
        deductions_data = [['Description', 'Amount']]
        deduction_items = [
            ('Income Tax (PAYE)', data.get('income_tax', '0')),
            ('Employee NI', data.get('employee_ni', '0')),
            ('Umbrella Fee', data.get('umbrella_fee', '0')),
            ('Pension', data.get('pension', '0')),
        ]
        if data.get('student_loan', '0') not in ('0', '0.00', 0):
            deduction_items.append(('Student Loan', data.get('student_loan', '0')))

        for name, amount in deduction_items:
            deductions_data.append([name, f"£{amount}"])

        deductions_table = Table(deductions_data, colWidths=[380, 100])
        deductions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fce4ec')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(deductions_table)
        elements.append(Spacer(1, 6 * mm))

        # Net Pay
        net_pay_table = Table(
            [['NET PAY', f"£{data.get('net_pay', '0')}"]],
            colWidths=[380, 100],
        )
        net_pay_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(net_pay_table)
        elements.append(Spacer(1, 8 * mm))

        # Footer
        elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(
            'This payslip is generated by the Agentic Umbrella Platform. '
            'Retain for your records. Queries: contact your umbrella company.',
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=colors.grey),
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _build_p45_pdf(data: dict) -> io.BytesIO:
        """Build a P45 leaving certificate PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'P45Title', parent=styles['Heading1'],
            fontSize=20, textColor=colors.HexColor('#b71c1c'),
        )

        elements = []
        elements.append(Paragraph('P45 — Details of Employee Leaving', title_style))
        elements.append(Spacer(1, 10 * mm))

        details = [
            ['Employer Name:', data.get('employer_name', '')],
            ['PAYE Reference:', data.get('paye_reference', '')],
            ['Employee Name:', data.get('employee_name', '')],
            ['NI Number:', data.get('ni_number', '')],
            ['Tax Code:', data.get('tax_code', '')],
            ['Leaving Date:', data.get('leaving_date', '')],
            ['Tax Year:', data.get('tax_year', '')],
            ['Total Pay to Date:', f"£{data.get('total_pay_ytd', '0')}"],
            ['Total Tax Deducted:', f"£{data.get('total_tax_ytd', '0')}"],
        ]

        table = Table(details, colWidths=[180, 300])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _build_p60_pdf(data: dict) -> io.BytesIO:
        """Build a P60 annual summary PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'P60Title', parent=styles['Heading1'],
            fontSize=20, textColor=colors.HexColor('#1b5e20'),
        )

        elements = []
        elements.append(Paragraph(
            f"P60 — End of Year Certificate — Tax Year {data.get('tax_year', '')}",
            title_style,
        ))
        elements.append(Spacer(1, 10 * mm))

        details = [
            ['Employer Name:', data.get('employer_name', '')],
            ['PAYE Reference:', data.get('paye_reference', '')],
            ['Employee Name:', data.get('employee_name', '')],
            ['NI Number:', data.get('ni_number', '')],
            ['Tax Code:', data.get('tax_code', '')],
            ['Total Pay in Year:', f"£{data.get('total_pay', '0')}"],
            ['Total Tax Deducted:', f"£{data.get('total_tax', '0')}"],
            ['Employee NI Contributions:', f"£{data.get('total_employee_ni', '0')}"],
            ['Employer NI Contributions:', f"£{data.get('total_employer_ni', '0')}"],
        ]

        table = Table(details, colWidths=[200, 280])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer
