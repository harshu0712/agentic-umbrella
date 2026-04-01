"""
Pre-Payroll Compliance Validation Service — Module 6

Performs all mandatory compliance checks BEFORE payroll is allowed to run.
If any check fails, payroll is blocked and an exception is raised.

Checks performed:
1. Contractor has a valid PAYE tax code
2. National Insurance number is present and valid
3. Umbrella company PAYE scheme is active
4. Gross pay anomaly detection (variance from historical average)
5. No unresolved exceptions on the work record
6. Working hours within acceptable range
7. Hourly rate meets National Living Wage minimum
"""

import logging
from decimal import Decimal

from django.db.models import Avg

from compliance.models import ComplianceCheck
from compliance.validators import validate_tax_code, validate_ni_number
from compliance.constants import ANOMALY_THRESHOLDS
from core.enums import (
    AuditEventType,
    ExceptionType,
    ExceptionSeverity,
    ExceptionStatus,
    WorkRecordState,
)
from audit.services import AuditService
from exceptions_handler.services import ExceptionService

logger = logging.getLogger('compliance')


class ComplianceValidationService:
    """
    Pre-payroll compliance validation.

    Usage:
        from compliance.services import ComplianceValidationService

        result = ComplianceValidationService.validate(work_record)
        if not result.all_passed:
            # Payroll is blocked
            print(result.checks)
    """

    @staticmethod
    def validate(work_record) -> ComplianceCheck:
        """
        Run the full pre-payroll compliance validation suite.

        Returns a ComplianceCheck record with detailed results.
        If any check fails, an exception is raised and payroll is blocked.
        """
        checks = []

        # Get contractor link
        try:
            contractor_link = work_record.contractor.contractor_link
        except Exception:
            contractor_link = None

        # Check 1: Valid PAYE tax code
        checks.append(
            ComplianceValidationService._check_tax_code(contractor_link)
        )

        # Check 2: Valid NI number
        checks.append(
            ComplianceValidationService._check_ni_number(contractor_link)
        )

        # Check 3: PAYE scheme active
        checks.append(
            ComplianceValidationService._check_paye_scheme(work_record.umbrella)
        )

        # Check 4: Gross pay anomaly detection
        checks.append(
            ComplianceValidationService._check_gross_pay_anomaly(work_record)
        )

        # Check 5: No blocking exceptions
        checks.append(
            ComplianceValidationService._check_no_blocking_exceptions(work_record)
        )

        # Check 6: Working hours within range
        checks.append(
            ComplianceValidationService._check_working_hours(work_record)
        )

        # Check 7: Hourly rate meets minimum wage
        checks.append(
            ComplianceValidationService._check_minimum_wage(work_record)
        )

        # Check 8: Work record in correct state
        checks.append(
            ComplianceValidationService._check_work_record_state(work_record)
        )

        # Calculate results
        all_passed = all(c['passed'] for c in checks)
        failed_count = sum(1 for c in checks if not c['passed'])

        # Save compliance check record
        compliance_check = ComplianceCheck.objects.create(
            work_record=work_record,
            contractor=work_record.contractor,
            organisation=work_record.umbrella,
            checks=checks,
            all_passed=all_passed,
            failed_checks_count=failed_count,
        )

        # Audit log
        event_type = (
            AuditEventType.COMPLIANCE_CHECK_PASSED if all_passed
            else AuditEventType.COMPLIANCE_CHECK_FAILED
        )
        AuditService.log(
            event_type=event_type,
            work_record=work_record,
            organisation=work_record.umbrella,
            metadata={
                'compliance_check_id': str(compliance_check.id),
                'all_passed': all_passed,
                'failed_count': failed_count,
                'checks': checks,
            },
        )

        # If failed, raise exception to block workflow
        if not all_passed:
            failed_details = [c for c in checks if not c['passed']]
            ExceptionService.raise_exception(
                exception_type=ExceptionType.COMPLIANCE_VALIDATION_FAILURE,
                title=f'Pre-payroll compliance validation failed ({failed_count} issues)',
                description=(
                    f"Compliance validation for Work Record {work_record.id} failed. "
                    f"Failed checks: {', '.join(c['check'] for c in failed_details)}"
                ),
                work_record=work_record,
                severity=ExceptionSeverity.HIGH,
                context_data={
                    'compliance_check_id': str(compliance_check.id),
                    'failed_checks': failed_details,
                },
            )

            logger.warning(
                'Compliance validation FAILED for WR-%s: %d checks failed',
                str(work_record.id)[:8], failed_count,
            )
        else:
            logger.info(
                'Compliance validation PASSED for WR-%s',
                str(work_record.id)[:8],
            )

        return compliance_check

    @staticmethod
    def _check_tax_code(contractor_link) -> dict:
        """Check if contractor has a valid PAYE tax code."""
        if not contractor_link:
            return {
                'check': 'tax_code_valid',
                'passed': False,
                'detail': 'Contractor link not found. Cannot verify tax code.',
            }

        result = validate_tax_code(contractor_link.tax_code)
        return {
            'check': 'tax_code_valid',
            'passed': result['valid'],
            'detail': result['detail'],
        }

    @staticmethod
    def _check_ni_number(contractor_link) -> dict:
        """Check if contractor has a valid NI number."""
        if not contractor_link:
            return {
                'check': 'ni_number_valid',
                'passed': False,
                'detail': 'Contractor link not found. Cannot verify NI number.',
            }

        result = validate_ni_number(contractor_link.ni_number)
        return {
            'check': 'ni_number_valid',
            'passed': result['valid'],
            'detail': result['detail'],
        }

    @staticmethod
    def _check_paye_scheme(umbrella) -> dict:
        """Check if the umbrella company's PAYE scheme is active."""
        if not umbrella.paye_scheme_active:
            return {
                'check': 'paye_scheme_active',
                'passed': False,
                'detail': (
                    f"Umbrella company '{umbrella.name}' PAYE scheme is INACTIVE. "
                    f"Reference: {umbrella.paye_reference}"
                ),
            }

        if not umbrella.paye_reference:
            return {
                'check': 'paye_scheme_active',
                'passed': False,
                'detail': f"Umbrella company '{umbrella.name}' has no PAYE reference.",
            }

        return {
            'check': 'paye_scheme_active',
            'passed': True,
            'detail': f"PAYE scheme active. Reference: {umbrella.paye_reference}",
        }

    @staticmethod
    def _check_gross_pay_anomaly(work_record) -> dict:
        """Check if gross pay is within expected range compared to history."""
        from core.models import WorkRecord

        # Get historical average for this contractor
        historical_avg = WorkRecord.objects.filter(
            contractor=work_record.contractor,
            state__in=[
                WorkRecordState.PAYROLL_COMPLETED,
                WorkRecordState.COMPLIANCE_SUBMITTED,
                WorkRecordState.COMPLETED,
            ],
        ).exclude(
            id=work_record.id
        ).aggregate(
            avg_gross=Avg('gross_amount')
        )['avg_gross']

        if historical_avg is None:
            # First record — no historical data to compare
            return {
                'check': 'gross_pay_anomaly',
                'passed': True,
                'detail': 'No historical data for comparison. First work record.',
            }

        variance_pct = abs(
            (float(work_record.gross_amount) - float(historical_avg))
            / float(historical_avg) * 100
        )
        threshold = ANOMALY_THRESHOLDS['gross_pay_variance_pct']

        if variance_pct > threshold:
            return {
                'check': 'gross_pay_anomaly',
                'passed': False,
                'detail': (
                    f"Gross pay £{work_record.gross_amount} deviates {variance_pct:.1f}% "
                    f"from historical average £{historical_avg:.2f} "
                    f"(threshold: {threshold}%)."
                ),
            }

        return {
            'check': 'gross_pay_anomaly',
            'passed': True,
            'detail': (
                f"Gross pay within expected range. "
                f"Variance: {variance_pct:.1f}% (threshold: {threshold}%)."
            ),
        }

    @staticmethod
    def _check_no_blocking_exceptions(work_record) -> dict:
        """Check if there are unresolved exceptions blocking this work record."""
        from exceptions_handler.models import PlatformException

        blocking = PlatformException.objects.filter(
            work_record=work_record,
        ).exclude(
            status=ExceptionStatus.RESOLVED,
        ).count()

        if blocking > 0:
            return {
                'check': 'no_blocking_exceptions',
                'passed': False,
                'detail': f'{blocking} unresolved exception(s) blocking this work record.',
            }

        return {
            'check': 'no_blocking_exceptions',
            'passed': True,
            'detail': 'No unresolved exceptions.',
        }

    @staticmethod
    def _check_working_hours(work_record) -> dict:
        """Check if declared hours are within acceptable range."""
        max_hours = ANOMALY_THRESHOLDS['max_weekly_hours']
        hours = float(work_record.hours_worked)

        if hours <= 0:
            return {
                'check': 'working_hours_valid',
                'passed': False,
                'detail': f'Hours worked ({hours}) must be greater than zero.',
            }

        if hours > max_hours:
            return {
                'check': 'working_hours_valid',
                'passed': False,
                'detail': (
                    f'Declared hours ({hours}) exceed maximum threshold '
                    f'({max_hours} hours/week). Manual review required.'
                ),
            }

        return {
            'check': 'working_hours_valid',
            'passed': True,
            'detail': f'Hours worked ({hours}) within acceptable range.',
        }

    @staticmethod
    def _check_minimum_wage(work_record) -> dict:
        """Check hourly rate meets National Living Wage minimum."""
        min_rate = Decimal(str(ANOMALY_THRESHOLDS['min_hourly_rate']))

        if work_record.hourly_rate < min_rate:
            return {
                'check': 'minimum_wage_compliant',
                'passed': False,
                'detail': (
                    f'Hourly rate (£{work_record.hourly_rate}) is below '
                    f'National Living Wage (£{min_rate}).'
                ),
            }

        return {
            'check': 'minimum_wage_compliant',
            'passed': True,
            'detail': f'Hourly rate (£{work_record.hourly_rate}) meets minimum wage.',
        }

    @staticmethod
    def _check_work_record_state(work_record) -> dict:
        """Check work record is in the correct state for payroll."""
        if work_record.state != WorkRecordState.PAYMENT_RECEIVED:
            return {
                'check': 'work_record_state_valid',
                'passed': False,
                'detail': (
                    f'Work record is in state {work_record.state}. '
                    f'Must be PAYMENT_RECEIVED before payroll can run.'
                ),
            }

        return {
            'check': 'work_record_state_valid',
            'passed': True,
            'detail': 'Work record is in PAYMENT_RECEIVED state.',
        }
