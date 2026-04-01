"""
Notification Matrix — Module 7

Maps platform events to the roles that should be notified.
This is the single source of truth for "who gets notified about what."

Based directly on the platform specification's notification table.
"""

from core.enums import AuditEventType, UserRole


# Event → list of roles to notify
NOTIFICATION_MATRIX = {
    AuditEventType.TIMESHEET_SUBMITTED: [
        UserRole.AGENCY_ADMIN,
        UserRole.AGENCY_CONSULTANT,
    ],
    AuditEventType.TIMESHEET_APPROVED: [
        UserRole.CONTRACTOR,
    ],
    AuditEventType.TIMESHEET_REJECTED: [
        UserRole.CONTRACTOR,
    ],
    AuditEventType.INVOICE_GENERATED: [
        UserRole.AGENCY_ADMIN,
    ],
    AuditEventType.INVOICE_APPROVED: [
        UserRole.UMBRELLA_ADMIN,
        UserRole.PAYROLL_OPERATOR,
    ],
    AuditEventType.PAYMENT_RECEIVED: [
        UserRole.UMBRELLA_ADMIN,
        UserRole.PAYROLL_OPERATOR,
    ],
    AuditEventType.PAYROLL_COMPLETED: [
        UserRole.CONTRACTOR,
        UserRole.UMBRELLA_ADMIN,
        UserRole.AGENCY_ADMIN,
    ],
    AuditEventType.RTI_SUBMISSION_SENT: [
        UserRole.UMBRELLA_ADMIN,
        UserRole.AGENCY_ADMIN,
        UserRole.CONTRACTOR,
    ],
    AuditEventType.EXCEPTION_RAISED: [
        UserRole.PLATFORM_ADMIN,
        UserRole.UMBRELLA_ADMIN,
    ],
    AuditEventType.EXCEPTION_RESOLVED: [
        UserRole.PLATFORM_ADMIN,
        UserRole.UMBRELLA_ADMIN,
    ],
    AuditEventType.COMPLIANCE_CHECK_FAILED: [
        UserRole.UMBRELLA_ADMIN,
        UserRole.PAYROLL_OPERATOR,
    ],
    AuditEventType.PAYROLL_BLOCKED: [
        UserRole.UMBRELLA_ADMIN,
        UserRole.PAYROLL_OPERATOR,
    ],
}


# Human-readable notification messages per event type
NOTIFICATION_MESSAGES = {
    AuditEventType.TIMESHEET_SUBMITTED: {
        'title': 'New Timesheet Submitted',
        'message': 'A contractor has submitted a timesheet for review. '
                   'Period: {period_start} to {period_end}.',
    },
    AuditEventType.TIMESHEET_APPROVED: {
        'title': 'Timesheet Approved',
        'message': 'Your timesheet for {period_start} to {period_end} '
                   'has been approved. An invoice will be generated automatically.',
    },
    AuditEventType.TIMESHEET_REJECTED: {
        'title': 'Timesheet Rejected',
        'message': 'Your timesheet for {period_start} to {period_end} '
                   'has been rejected. Reason: {rejection_reason}',
    },
    AuditEventType.INVOICE_GENERATED: {
        'title': 'Invoice Generated',
        'message': 'An invoice of £{amount} has been generated for '
                   'review and approval.',
    },
    AuditEventType.INVOICE_APPROVED: {
        'title': 'Invoice Approved',
        'message': 'Invoice #{invoice_ref} has been approved. '
                   'Payment is expected shortly.',
    },
    AuditEventType.PAYMENT_RECEIVED: {
        'title': 'Payment Received',
        'message': 'Payment of £{amount} has been received and reconciled. '
                   'Payroll processing will begin automatically.',
    },
    AuditEventType.PAYROLL_COMPLETED: {
        'title': 'Payroll Completed',
        'message': 'Payroll has been processed. Net pay of £{net_pay} '
                   'will be disbursed to the contractor.',
    },
    AuditEventType.RTI_SUBMISSION_SENT: {
        'title': 'HMRC Compliance Submitted',
        'message': 'RTI submission ({submission_type}) has been sent to HMRC. '
                   'All tax obligations have been filed.',
    },
    AuditEventType.EXCEPTION_RAISED: {
        'title': '⚠️ Exception Raised',
        'message': 'An exception has been raised: {description}. '
                   'Workflow is blocked until resolved.',
    },
    AuditEventType.EXCEPTION_RESOLVED: {
        'title': 'Exception Resolved',
        'message': 'Exception has been resolved. Workflow has been unblocked.',
    },
    AuditEventType.COMPLIANCE_CHECK_FAILED: {
        'title': 'Compliance Validation Failed',
        'message': 'Pre-payroll compliance check failed. '
                   'Payroll is blocked until issues are resolved.',
    },
    AuditEventType.PAYROLL_BLOCKED: {
        'title': 'Payroll Blocked',
        'message': 'Payroll cannot proceed. Payment has not been confirmed. '
                   'Current state: {current_state}.',
    },
}
