"""
Enumerations for the Agentic Umbrella Platform.

Defines all state machines, role types, and categorical constants
used across Module 6 (Compliance) and Module 7 (Audit, Notifications, Exceptions).
"""

from django.db import models


class OrganisationType(models.TextChoices):
    """Types of organisations on the platform."""
    AGENCY = 'AGENCY', 'Agency'
    UMBRELLA = 'UMBRELLA', 'Umbrella Company'


class UserRole(models.TextChoices):
    """Roles a user can hold within an organisation."""
    PLATFORM_ADMIN = 'PLATFORM_ADMIN', 'Platform Admin'
    AGENCY_ADMIN = 'AGENCY_ADMIN', 'Agency Admin'
    AGENCY_CONSULTANT = 'AGENCY_CONSULTANT', 'Agency Consultant'
    UMBRELLA_ADMIN = 'UMBRELLA_ADMIN', 'Umbrella Admin'
    PAYROLL_OPERATOR = 'PAYROLL_OPERATOR', 'Payroll Operator'
    CONTRACTOR = 'CONTRACTOR', 'Contractor'


class WorkRecordState(models.TextChoices):
    """
    The master state machine for a Work Record.

    Defines the full lifecycle from timesheet submission through to
    compliance completion. Every transition must be validated and audit-logged.

    Flow:
    WORK_SUBMITTED → WORK_APPROVED → INVOICE_GENERATED → INVOICE_APPROVED →
    PAYMENT_PENDING → PAYMENT_RECEIVED → PAYROLL_PROCESSING → PAYROLL_COMPLETED →
    COMPLIANCE_SUBMITTED → COMPLETED

    Side path: WORK_SUBMITTED → WORK_REJECTED → WORK_SUBMITTED (resubmit)
    """
    WORK_SUBMITTED = 'WORK_SUBMITTED', 'Work Submitted'
    WORK_APPROVED = 'WORK_APPROVED', 'Work Approved'
    WORK_REJECTED = 'WORK_REJECTED', 'Work Rejected'
    INVOICE_GENERATED = 'INVOICE_GENERATED', 'Invoice Generated'
    INVOICE_APPROVED = 'INVOICE_APPROVED', 'Invoice Approved'
    PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
    PAYROLL_PROCESSING = 'PAYROLL_PROCESSING', 'Payroll Processing'
    PAYROLL_COMPLETED = 'PAYROLL_COMPLETED', 'Payroll Completed'
    COMPLIANCE_SUBMITTED = 'COMPLIANCE_SUBMITTED', 'Compliance Submitted'
    COMPLETED = 'COMPLETED', 'Completed'


# Valid state transitions — the state machine rules
VALID_STATE_TRANSITIONS = {
    WorkRecordState.WORK_SUBMITTED: [
        WorkRecordState.WORK_APPROVED,
        WorkRecordState.WORK_REJECTED,
    ],
    WorkRecordState.WORK_REJECTED: [
        WorkRecordState.WORK_SUBMITTED,  # Resubmission
    ],
    WorkRecordState.WORK_APPROVED: [
        WorkRecordState.INVOICE_GENERATED,
    ],
    WorkRecordState.INVOICE_GENERATED: [
        WorkRecordState.INVOICE_APPROVED,
    ],
    WorkRecordState.INVOICE_APPROVED: [
        WorkRecordState.PAYMENT_PENDING,
    ],
    WorkRecordState.PAYMENT_PENDING: [
        WorkRecordState.PAYMENT_RECEIVED,
    ],
    WorkRecordState.PAYMENT_RECEIVED: [
        WorkRecordState.PAYROLL_PROCESSING,
    ],
    WorkRecordState.PAYROLL_PROCESSING: [
        WorkRecordState.PAYROLL_COMPLETED,
    ],
    WorkRecordState.PAYROLL_COMPLETED: [
        WorkRecordState.COMPLIANCE_SUBMITTED,
    ],
    WorkRecordState.COMPLIANCE_SUBMITTED: [
        WorkRecordState.COMPLETED,
    ],
    WorkRecordState.COMPLETED: [],  # Terminal state
}


class NotificationChannel(models.TextChoices):
    """Channels through which notifications can be delivered."""
    EMAIL = 'EMAIL', 'Email'
    IN_APP = 'IN_APP', 'In-App'


class NotificationStatus(models.TextChoices):
    """Status of a notification delivery."""
    PENDING = 'PENDING', 'Pending'
    SENT = 'SENT', 'Sent'
    FAILED = 'FAILED', 'Failed'


class ExceptionSeverity(models.TextChoices):
    """Severity levels for platform exceptions."""
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical'


class ExceptionStatus(models.TextChoices):
    """Lifecycle states for exception resolution."""
    RAISED = 'RAISED', 'Raised'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    IN_REVIEW = 'IN_REVIEW', 'In Review'
    ESCALATED = 'ESCALATED', 'Escalated'
    RESOLVED = 'RESOLVED', 'Resolved'


class ExceptionType(models.TextChoices):
    """Categorisation of platform exceptions."""
    PAYMENT_MISMATCH = 'PAYMENT_MISMATCH', 'Payment Amount Mismatch'
    MISSING_TAX_CODE = 'MISSING_TAX_CODE', 'Missing or Invalid Tax Code'
    INVALID_NI_NUMBER = 'INVALID_NI_NUMBER', 'Invalid National Insurance Number'
    UNKNOWN_PAYMENT_SOURCE = 'UNKNOWN_PAYMENT_SOURCE', 'Unknown Payment Source'
    PAYROLL_ANOMALY = 'PAYROLL_ANOMALY', 'Payroll Calculation Anomaly'
    HMRC_SUBMISSION_ERROR = 'HMRC_SUBMISSION_ERROR', 'HMRC Submission Error'
    COMPLIANCE_VALIDATION_FAILURE = 'COMPLIANCE_VALIDATION_FAILURE', 'Compliance Validation Failure'
    PAYE_SCHEME_INACTIVE = 'PAYE_SCHEME_INACTIVE', 'PAYE Scheme Inactive'
    GENERAL = 'GENERAL', 'General Exception'


class RTISubmissionType(models.TextChoices):
    """Types of Real Time Information submissions to HMRC."""
    FPS = 'FPS', 'Full Payment Submission'
    EPS = 'EPS', 'Employer Payment Summary'


class RTISubmissionStatus(models.TextChoices):
    """Status of an RTI submission."""
    PENDING = 'PENDING', 'Pending'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    REJECTED = 'REJECTED', 'Rejected'
    FAILED = 'FAILED', 'Failed'


class StatutoryDocumentType(models.TextChoices):
    """Types of statutory documents."""
    PAYSLIP = 'PAYSLIP', 'Payslip'
    P45 = 'P45', 'P45 - Leaving Certificate'
    P60 = 'P60', 'P60 - Annual Summary'


class AuditEventType(models.TextChoices):
    """All auditable event types across the platform."""
    # Identity events
    USER_CREATED = 'USER_CREATED', 'User Created'
    USER_UPDATED = 'USER_UPDATED', 'User Updated'
    USER_ROLE_CHANGED = 'USER_ROLE_CHANGED', 'User Role Changed'
    USER_LOGIN = 'USER_LOGIN', 'User Login'
    USER_LOGOUT = 'USER_LOGOUT', 'User Logout'

    # Work Record state transitions
    TIMESHEET_SUBMITTED = 'TIMESHEET_SUBMITTED', 'Timesheet Submitted'
    TIMESHEET_APPROVED = 'TIMESHEET_APPROVED', 'Timesheet Approved'
    TIMESHEET_REJECTED = 'TIMESHEET_REJECTED', 'Timesheet Rejected'
    INVOICE_GENERATED = 'INVOICE_GENERATED', 'Invoice Generated'
    INVOICE_APPROVED = 'INVOICE_APPROVED', 'Invoice Approved'
    PAYMENT_INITIATED = 'PAYMENT_INITIATED', 'Payment Initiated'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
    PAYROLL_STARTED = 'PAYROLL_STARTED', 'Payroll Started'
    PAYROLL_COMPLETED = 'PAYROLL_COMPLETED', 'Payroll Completed'
    PAYROLL_BLOCKED = 'PAYROLL_BLOCKED', 'Payroll Blocked'

    # Compliance events
    COMPLIANCE_CHECK_PASSED = 'COMPLIANCE_CHECK_PASSED', 'Compliance Check Passed'
    COMPLIANCE_CHECK_FAILED = 'COMPLIANCE_CHECK_FAILED', 'Compliance Check Failed'
    RTI_SUBMISSION_SENT = 'RTI_SUBMISSION_SENT', 'RTI Submission Sent'
    RTI_SUBMISSION_ACCEPTED = 'RTI_SUBMISSION_ACCEPTED', 'RTI Submission Accepted'
    RTI_SUBMISSION_REJECTED = 'RTI_SUBMISSION_REJECTED', 'RTI Submission Rejected'
    DOCUMENT_GENERATED = 'DOCUMENT_GENERATED', 'Document Generated'

    # Exception events
    EXCEPTION_RAISED = 'EXCEPTION_RAISED', 'Exception Raised'
    EXCEPTION_ASSIGNED = 'EXCEPTION_ASSIGNED', 'Exception Assigned'
    EXCEPTION_ESCALATED = 'EXCEPTION_ESCALATED', 'Exception Escalated'
    EXCEPTION_RESOLVED = 'EXCEPTION_RESOLVED', 'Exception Resolved'
    MANUAL_OVERRIDE = 'MANUAL_OVERRIDE', 'Manual Override Applied'

    # Notification events
    NOTIFICATION_SENT = 'NOTIFICATION_SENT', 'Notification Sent'
    NOTIFICATION_FAILED = 'NOTIFICATION_FAILED', 'Notification Failed'

    # Configuration events
    CONFIG_CHANGED = 'CONFIG_CHANGED', 'Configuration Changed'
