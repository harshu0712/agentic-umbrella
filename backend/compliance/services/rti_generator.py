"""
RTI (Real Time Information) Generator Service — Module 6

Generates FPS (Full Payment Submission) and EPS (Employer Payment Summary)
payloads for HMRC submission. Includes submission tracking and retry logic.
"""

import logging
from datetime import date
from decimal import Decimal

from django.utils import timezone

from compliance.models import RTISubmission
from compliance.constants import (
    TAX_BANDS,
    EMPLOYEE_NI,
    EMPLOYER_NI,
    PERSONAL_ALLOWANCE,
    HMRC_RTI,
)
from core.enums import (
    RTISubmissionType,
    RTISubmissionStatus,
    AuditEventType,
)
from audit.services import AuditService
from notifications.services import NotificationDispatcher

logger = logging.getLogger('compliance')


class RTIGeneratorService:
    """
    Generates and tracks RTI submissions to HMRC.

    In production, the submit() method would call the HMRC API.
    For development, it uses a mock endpoint that simulates responses.
    """

    @staticmethod
    def generate_fps(work_record, payroll_data: dict) -> RTISubmission:
        """
        Generate a Full Payment Submission (FPS) for a work record.

        FPS must be submitted on or before payday for each employee payment.

        Args:
            work_record: The WorkRecord being paid
            payroll_data: Dict containing gross, tax, ni, net amounts
        """
        contractor_link = work_record.contractor.contractor_link
        umbrella = work_record.umbrella

        # Determine tax year and period
        tax_year, tax_period = RTIGeneratorService._get_tax_period(
            work_record.period_end
        )

        # Build FPS payload (HMRC XML/JSON format simplified)
        payload = {
            'submission_type': 'FPS',
            'employer': {
                'paye_reference': umbrella.paye_reference,
                'name': umbrella.name,
            },
            'employee': {
                'ni_number': contractor_link.ni_number,
                'name': {
                    'first_name': work_record.contractor.first_name,
                    'last_name': work_record.contractor.last_name,
                },
                'tax_code': contractor_link.tax_code,
            },
            'payment': {
                'pay_date': str(work_record.period_end),
                'tax_year': tax_year,
                'tax_period': tax_period,
                'gross_pay_period': str(payroll_data.get('gross_pay', 0)),
                'gross_pay_ytd': str(payroll_data.get('gross_pay_ytd', 0)),
                'tax_deducted_period': str(payroll_data.get('income_tax', 0)),
                'tax_deducted_ytd': str(payroll_data.get('income_tax_ytd', 0)),
                'employee_ni_period': str(payroll_data.get('employee_ni', 0)),
                'employee_ni_ytd': str(payroll_data.get('employee_ni_ytd', 0)),
                'employer_ni_period': str(payroll_data.get('employer_ni', 0)),
                'employer_ni_ytd': str(payroll_data.get('employer_ni_ytd', 0)),
                'net_pay': str(payroll_data.get('net_pay', 0)),
                'hours_worked': str(work_record.hours_worked),
            },
            'deductions': payroll_data.get('deductions_breakdown', {}),
        }

        # Create submission record
        submission = RTISubmission.objects.create(
            submission_type=RTISubmissionType.FPS,
            work_record=work_record,
            organisation=umbrella,
            contractor=work_record.contractor,
            payload=payload,
            tax_year=tax_year,
            tax_period=tax_period,
            status=RTISubmissionStatus.PENDING,
        )

        logger.info(
            'FPS generated for WR-%s, tax period %s P%d',
            str(work_record.id)[:8], tax_year, tax_period,
        )

        return submission

    @staticmethod
    def generate_eps(organisation, tax_year: str, tax_period: int,
                     summary_data: dict) -> RTISubmission:
        """
        Generate an Employer Payment Summary (EPS).

        EPS is submitted monthly to report employer NI totals,
        statutory payment recoveries, and other adjustments.
        """
        payload = {
            'submission_type': 'EPS',
            'employer': {
                'paye_reference': organisation.paye_reference,
                'name': organisation.name,
            },
            'period': {
                'tax_year': tax_year,
                'tax_period': tax_period,
            },
            'summary': {
                'total_employer_ni': str(summary_data.get('total_employer_ni', 0)),
                'total_employee_ni': str(summary_data.get('total_employee_ni', 0)),
                'total_income_tax': str(summary_data.get('total_income_tax', 0)),
                'total_gross_pay': str(summary_data.get('total_gross_pay', 0)),
                'number_of_employees': summary_data.get('employee_count', 0),
                'apprenticeship_levy': str(summary_data.get('apprenticeship_levy', 0)),
                'employment_allowance_indicator': summary_data.get(
                    'employment_allowance', False
                ),
            },
        }

        submission = RTISubmission.objects.create(
            submission_type=RTISubmissionType.EPS,
            organisation=organisation,
            payload=payload,
            tax_year=tax_year,
            tax_period=tax_period,
            status=RTISubmissionStatus.PENDING,
        )

        logger.info(
            'EPS generated for %s, tax period %s P%d',
            organisation.name, tax_year, tax_period,
        )

        return submission

    @staticmethod
    def submit(submission_id) -> RTISubmission:
        """
        Submit an RTI record to HMRC.

        In production: calls HMRC API endpoint.
        In development: simulates a successful submission.
        """
        submission = RTISubmission.objects.get(id=submission_id)

        if submission.status not in [
            RTISubmissionStatus.PENDING,
            RTISubmissionStatus.FAILED,
        ]:
            raise ValueError(
                f'Cannot submit RTI in status {submission.status}.'
            )

        try:
            # === MOCK HMRC SUBMISSION ===
            # In production, replace with actual HMRC API call
            response = RTIGeneratorService._mock_hmrc_submit(submission)

            if response['accepted']:
                submission.status = RTISubmissionStatus.ACCEPTED
                submission.response_data = response
                submission.submitted_at = timezone.now()
                submission.responded_at = timezone.now()
                submission.save(update_fields=[
                    'status', 'response_data', 'submitted_at',
                    'responded_at',
                ])

                # Audit log
                AuditService.log(
                    event_type=AuditEventType.RTI_SUBMISSION_ACCEPTED,
                    work_record=submission.work_record,
                    organisation=submission.organisation,
                    metadata={
                        'submission_id': str(submission.id),
                        'submission_type': submission.submission_type,
                        'hmrc_response': response,
                    },
                )

                # Notify stakeholders
                NotificationDispatcher.dispatch(
                    event_type=AuditEventType.RTI_SUBMISSION_SENT,
                    work_record=submission.work_record,
                    context={
                        'submission_type': submission.get_submission_type_display(),
                    },
                )

                logger.info(
                    'RTI %s submission accepted by HMRC', submission.id,
                )
            else:
                submission.status = RTISubmissionStatus.REJECTED
                submission.response_data = response
                submission.error_message = response.get('error', 'Unknown error')
                submission.responded_at = timezone.now()
                submission.retry_count += 1
                submission.save(update_fields=[
                    'status', 'response_data', 'error_message',
                    'responded_at', 'retry_count',
                ])

                AuditService.log(
                    event_type=AuditEventType.RTI_SUBMISSION_REJECTED,
                    work_record=submission.work_record,
                    organisation=submission.organisation,
                    metadata={
                        'submission_id': str(submission.id),
                        'error': response.get('error'),
                    },
                )

                logger.warning(
                    'RTI %s submission rejected: %s',
                    submission.id, response.get('error'),
                )

        except Exception as e:
            submission.status = RTISubmissionStatus.FAILED
            submission.error_message = str(e)
            submission.retry_count += 1
            submission.save(update_fields=[
                'status', 'error_message', 'retry_count',
            ])

            logger.error(
                'RTI %s submission failed: %s',
                submission.id, str(e), exc_info=True,
            )

        return submission

    @staticmethod
    def retry_failed_submissions():
        """Retry all failed submissions that haven't exceeded max retries."""
        retryable = RTISubmission.objects.filter(
            status__in=[RTISubmissionStatus.FAILED, RTISubmissionStatus.REJECTED],
        ).exclude(
            retry_count__gte=models.F('max_retries'),
        )

        results = []
        for submission in retryable:
            result = RTIGeneratorService.submit(submission.id)
            results.append(result)

        logger.info('Retried %d failed RTI submissions', len(results))
        return results

    @staticmethod
    def _get_tax_period(payment_date: date) -> tuple:
        """
        Determine tax year and period from a payment date.

        UK tax year runs 6 April to 5 April.
        Tax period 1 = April, 2 = May, ..., 12 = March.
        """
        year = payment_date.year
        month = payment_date.month

        # Tax year starts on April 6
        if month >= 4:
            tax_year_start = year
        else:
            tax_year_start = year - 1

        tax_year = f"{tax_year_start}-{str(tax_year_start + 1)[-2:]}"

        # Tax period: April = 1, May = 2, ..., March = 12
        if month >= 4:
            tax_period = month - 3
        else:
            tax_period = month + 9

        return tax_year, tax_period

    @staticmethod
    def _mock_hmrc_submit(submission) -> dict:
        """
        Mock HMRC submission endpoint for development.

        Simulates a successful submission 95% of the time.
        Replace with actual HMRC API integration in production.
        """
        import random

        # Simulate network delay
        import time
        time.sleep(0.1)

        # 95% success rate for testing
        if random.random() < 0.95:
            return {
                'accepted': True,
                'correlation_id': f'HMRC-{submission.id.hex[:12].upper()}',
                'message': 'Submission accepted successfully.',
                'timestamp': timezone.now().isoformat(),
            }
        else:
            return {
                'accepted': False,
                'error': 'HMRC validation error: Employee record not found.',
                'error_code': 'ERR_EMP_NOT_FOUND',
                'timestamp': timezone.now().isoformat(),
            }
