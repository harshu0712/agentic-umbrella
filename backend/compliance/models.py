"""
Compliance Models — Module 6

Models for compliance checks, RTI submissions, and statutory documents.
"""

import uuid
from django.db import models
from django.conf import settings

from core.enums import (
    RTISubmissionType,
    RTISubmissionStatus,
    StatutoryDocumentType,
)


class ComplianceCheck(models.Model):
    """
    Pre-payroll compliance validation results.

    Records the outcome of every compliance check performed
    before payroll is allowed to run. Failed checks block payroll
    and raise exceptions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_record = models.ForeignKey(
        'core.WorkRecord',
        on_delete=models.PROTECT,
        related_name='compliance_checks',
    )
    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='compliance_checks',
    )
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.PROTECT,
        related_name='compliance_checks',
    )

    # Check results
    checks = models.JSONField(
        help_text=(
            'Detailed results of each validation check. '
            'Format: [{"check": "tax_code_valid", "passed": true, "detail": "..."}]'
        ),
    )
    all_passed = models.BooleanField(
        db_index=True,
        help_text='Whether all checks passed successfully.',
    )
    failed_checks_count = models.PositiveIntegerField(default=0)

    # Timestamps
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_check'
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['work_record', '-checked_at']),
            models.Index(fields=['all_passed']),
        ]

    def __str__(self):
        status = '✅ PASSED' if self.all_passed else f'❌ FAILED ({self.failed_checks_count} issues)'
        return f"Compliance Check for WR-{str(self.work_record_id)[:8]} — {status}"


class RTISubmission(models.Model):
    """
    Real Time Information submission to HMRC.

    Tracks FPS (Full Payment Submission) and EPS (Employer Payment Summary)
    submissions with status tracking and retry handling.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Submission details
    submission_type = models.CharField(
        max_length=10,
        choices=RTISubmissionType.choices,
        db_index=True,
    )
    work_record = models.ForeignKey(
        'core.WorkRecord',
        on_delete=models.PROTECT,
        related_name='rti_submissions',
        null=True,
        blank=True,
        help_text='Related work record (for FPS). Null for monthly EPS.',
    )
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.PROTECT,
        related_name='rti_submissions',
    )
    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rti_submissions',
        null=True,
        blank=True,
    )

    # Payload & Response
    payload = models.JSONField(
        help_text='The RTI submission payload sent to HMRC.',
    )
    response_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Response received from HMRC.',
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=RTISubmissionStatus.choices,
        default=RTISubmissionStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)

    # Retry tracking
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)

    # Period
    tax_year = models.CharField(
        max_length=7,
        help_text='Tax year in format YYYY-YY (e.g., 2025-26)',
    )
    tax_period = models.PositiveIntegerField(
        help_text='Tax period number (1-12 for monthly)',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_rti_submission'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submission_type', 'status']),
            models.Index(fields=['organisation', '-created_at']),
            models.Index(fields=['tax_year', 'tax_period']),
        ]

    def __str__(self):
        return (
            f"{self.get_submission_type_display()} | "
            f"{self.tax_year} P{self.tax_period} | "
            f"{self.get_status_display()}"
        )

    @property
    def can_retry(self):
        return (
            self.status in [RTISubmissionStatus.FAILED, RTISubmissionStatus.REJECTED]
            and self.retry_count < self.max_retries
        )


class StatutoryDocument(models.Model):
    """
    Generated statutory documents — payslips, P45, P60.

    Documents must be retained for a minimum of 7 years
    as per UK employment law.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Document details
    document_type = models.CharField(
        max_length=20,
        choices=StatutoryDocumentType.choices,
        db_index=True,
    )
    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='statutory_documents',
    )
    work_record = models.ForeignKey(
        'core.WorkRecord',
        on_delete=models.PROTECT,
        related_name='statutory_documents',
        null=True,
        blank=True,
    )
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.PROTECT,
        related_name='statutory_documents',
    )

    # File storage
    file = models.FileField(
        upload_to='compliance/documents/%Y/%m/',
        help_text='Generated PDF document.',
    )
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(
        default=0,
        help_text='File size in bytes.',
    )

    # Financial data snapshot (stored for audit purposes)
    financial_data = models.JSONField(
        default=dict,
        help_text=(
            'Snapshot of financial data at time of generation. '
            'Includes gross pay, deductions, net pay, tax code, etc.'
        ),
    )

    # Period
    tax_year = models.CharField(max_length=7)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)

    # Retention
    retention_until = models.DateField(
        help_text='Document must be retained until this date (7-year minimum).',
    )

    class Meta:
        db_table = 'compliance_statutory_document'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['contractor', 'document_type']),
            models.Index(fields=['document_type', '-generated_at']),
            models.Index(fields=['tax_year']),
            models.Index(fields=['organisation', '-generated_at']),
        ]

    def __str__(self):
        return (
            f"{self.get_document_type_display()} | "
            f"{self.contractor.email} | {self.tax_year}"
        )


class ComplianceReport(models.Model):
    """
    Generated compliance reports for different user types.

    - Umbrella: payroll summaries, HMRC submission logs, liability reports
    - Agency: cost reports (gross charges vs net contractor pay)
    - Contractor: payslips, P60, P45 access
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Report details
    report_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Type of report (e.g., payroll_summary, cost_report, liability_report)',
    )
    title = models.CharField(max_length=255)
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.PROTECT,
        related_name='compliance_reports',
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='generated_reports',
        null=True,
        blank=True,
    )

    # Report data
    report_data = models.JSONField(
        help_text='The report content in structured format.',
    )
    period_start = models.DateField()
    period_end = models.DateField()

    # Generated PDF (optional)
    file = models.FileField(
        upload_to='compliance/reports/%Y/%m/',
        null=True,
        blank=True,
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_report'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', '-generated_at']),
            models.Index(fields=['organisation', '-generated_at']),
        ]

    def __str__(self):
        return f"{self.title} | {self.organisation.name} | {self.period_start} to {self.period_end}"
