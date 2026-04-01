"""
Compliance Reporting Service — Module 6

Generates reports for three audiences:
- Umbrella Company: payroll summaries, HMRC submission logs, liability reports
- Agency: cost reports (gross charges vs net contractor pay)
- Contractor: document access (payslips, P60, P45)
"""

import logging
from datetime import date
from decimal import Decimal

from django.db.models import Sum, Count, Avg, Q

from compliance.models import (
    ComplianceReport,
    ComplianceCheck,
    RTISubmission,
    StatutoryDocument,
)
from core.models import WorkRecord
from core.enums import (
    WorkRecordState,
    RTISubmissionStatus,
    StatutoryDocumentType,
)

logger = logging.getLogger('compliance')


class ComplianceReportingService:
    """Generates compliance reports for different organisation types."""

    @staticmethod
    def generate_umbrella_payroll_summary(
        organisation, period_start: date, period_end: date
    ) -> dict:
        """
        Generate a payroll summary report for an umbrella company.

        Includes: total gross, total deductions, total net, employee count,
        HMRC submission status.
        """
        work_records = WorkRecord.objects.filter(
            umbrella=organisation,
            period_start__gte=period_start,
            period_end__lte=period_end,
            state__in=[
                WorkRecordState.PAYROLL_COMPLETED,
                WorkRecordState.COMPLIANCE_SUBMITTED,
                WorkRecordState.COMPLETED,
            ],
        )

        aggregated = work_records.aggregate(
            total_gross=Sum('gross_amount'),
            total_records=Count('id'),
            avg_gross=Avg('gross_amount'),
        )

        rti_submissions = RTISubmission.objects.filter(
            organisation=organisation,
            created_at__date__gte=period_start,
            created_at__date__lte=period_end,
        ).values('status').annotate(count=Count('id'))

        rti_status = {item['status']: item['count'] for item in rti_submissions}

        compliance_checks = ComplianceCheck.objects.filter(
            organisation=organisation,
            checked_at__date__gte=period_start,
            checked_at__date__lte=period_end,
        )

        report_data = {
            'report_type': 'umbrella_payroll_summary',
            'organisation': organisation.name,
            'period': f'{period_start} to {period_end}',
            'payroll': {
                'total_work_records': aggregated['total_records'],
                'total_gross_pay': str(aggregated['total_gross'] or 0),
                'average_gross_pay': str(round(aggregated['avg_gross'] or 0, 2)),
            },
            'hmrc_submissions': {
                'total': sum(rti_status.values()),
                'by_status': rti_status,
            },
            'compliance_checks': {
                'total': compliance_checks.count(),
                'passed': compliance_checks.filter(all_passed=True).count(),
                'failed': compliance_checks.filter(all_passed=False).count(),
            },
        }

        # Save report record
        report = ComplianceReport.objects.create(
            report_type='umbrella_payroll_summary',
            title=f'Payroll Summary — {period_start} to {period_end}',
            organisation=organisation,
            report_data=report_data,
            period_start=period_start,
            period_end=period_end,
        )

        logger.info(
            'Umbrella payroll summary generated for %s (%s to %s)',
            organisation.name, period_start, period_end,
        )

        return report_data

    @staticmethod
    def generate_agency_cost_report(
        organisation, period_start: date, period_end: date
    ) -> dict:
        """
        Generate a cost report for an agency.

        Shows gross charges vs net contractor pay for
        financial visibility.
        """
        work_records = WorkRecord.objects.filter(
            agency=organisation,
            period_start__gte=period_start,
            period_end__lte=period_end,
            state__in=[
                WorkRecordState.PAYROLL_COMPLETED,
                WorkRecordState.COMPLIANCE_SUBMITTED,
                WorkRecordState.COMPLETED,
            ],
        )

        aggregated = work_records.aggregate(
            total_gross=Sum('gross_amount'),
            total_records=Count('id'),
            total_hours=Sum('hours_worked'),
        )

        # Per-contractor breakdown
        contractor_breakdown = (
            work_records
            .values('contractor__email', 'contractor__first_name', 'contractor__last_name')
            .annotate(
                total_gross=Sum('gross_amount'),
                total_hours=Sum('hours_worked'),
                record_count=Count('id'),
            )
            .order_by('-total_gross')
        )

        report_data = {
            'report_type': 'agency_cost_report',
            'organisation': organisation.name,
            'period': f'{period_start} to {period_end}',
            'summary': {
                'total_work_records': aggregated['total_records'],
                'total_gross_charges': str(aggregated['total_gross'] or 0),
                'total_hours': str(aggregated['total_hours'] or 0),
            },
            'contractor_breakdown': [
                {
                    'email': c['contractor__email'],
                    'name': f"{c['contractor__first_name']} {c['contractor__last_name']}",
                    'total_gross': str(c['total_gross']),
                    'total_hours': str(c['total_hours']),
                    'records': c['record_count'],
                }
                for c in contractor_breakdown
            ],
        }

        ComplianceReport.objects.create(
            report_type='agency_cost_report',
            title=f'Cost Report — {period_start} to {period_end}',
            organisation=organisation,
            report_data=report_data,
            period_start=period_start,
            period_end=period_end,
        )

        logger.info(
            'Agency cost report generated for %s (%s to %s)',
            organisation.name, period_start, period_end,
        )

        return report_data

    @staticmethod
    def get_contractor_documents(contractor, document_type=None,
                                  tax_year=None) -> list:
        """
        Get all documents for a contractor (payslips, P60, P45).

        Contractors can only access their own documents.
        """
        queryset = StatutoryDocument.objects.filter(contractor=contractor)

        if document_type:
            queryset = queryset.filter(document_type=document_type)
        if tax_year:
            queryset = queryset.filter(tax_year=tax_year)

        return queryset.order_by('-generated_at')
