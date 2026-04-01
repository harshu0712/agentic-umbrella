"""
Audit Service — centralised logging utility.

This is the single entry point for creating audit log entries.
Every module calls AuditService.log() to record events.
"""

import uuid
import logging
from threading import local

from audit.models import AuditLog
from core.enums import AuditEventType

logger = logging.getLogger('audit')

# Thread-local storage for request context (populated by middleware)
_audit_context = local()


def set_audit_context(actor=None, actor_role='', organisation=None,
                      ip_address=None, user_agent='', request_id=None):
    """Set the audit context for the current request (called by middleware)."""
    _audit_context.actor = actor
    _audit_context.actor_role = actor_role
    _audit_context.organisation = organisation
    _audit_context.ip_address = ip_address
    _audit_context.user_agent = user_agent
    _audit_context.request_id = request_id or str(uuid.uuid4())[:16]


def clear_audit_context():
    """Clear the audit context after the request is complete."""
    for attr in ['actor', 'actor_role', 'organisation', 'ip_address',
                 'user_agent', 'request_id']:
        if hasattr(_audit_context, attr):
            delattr(_audit_context, attr)


def get_audit_context():
    """Retrieve the current audit context."""
    return {
        'actor': getattr(_audit_context, 'actor', None),
        'actor_role': getattr(_audit_context, 'actor_role', ''),
        'organisation': getattr(_audit_context, 'organisation', None),
        'ip_address': getattr(_audit_context, 'ip_address', None),
        'user_agent': getattr(_audit_context, 'user_agent', ''),
        'request_id': getattr(_audit_context, 'request_id', ''),
    }


class AuditService:
    """
    Centralised audit logging service.

    Usage:
        from audit.services import AuditService

        AuditService.log(
            event_type=AuditEventType.TIMESHEET_APPROVED,
            work_record=work_record,
            before_state='WORK_SUBMITTED',
            after_state='WORK_APPROVED',
            metadata={'approved_by': user.email}
        )
    """

    @staticmethod
    def log(
        event_type: str,
        actor=None,
        actor_role: str = '',
        organisation=None,
        work_record=None,
        before_state: str = '',
        after_state: str = '',
        metadata: dict = None,
        ip_address: str = None,
        user_agent: str = '',
        request_id: str = '',
    ) -> AuditLog:
        """
        Create an immutable audit log entry.

        If actor/organisation/ip_address are not provided, they are
        pulled from the request context (set by AuditContextMiddleware).
        """
        context = get_audit_context()

        # Use provided values or fall back to request context
        actor = actor or context.get('actor')
        actor_role = actor_role or context.get('actor_role', '')
        organisation = organisation or context.get('organisation')
        ip_address = ip_address or context.get('ip_address')
        user_agent = user_agent or context.get('user_agent', '')
        request_id = request_id or context.get('request_id', '')

        # Auto-detect actor role from user object
        if not actor_role and actor and hasattr(actor, 'role'):
            actor_role = actor.role

        entry = AuditLog.objects.create(
            event_type=event_type,
            actor=actor,
            actor_role=actor_role,
            organisation=organisation,
            work_record=work_record,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        logger.info(
            'Audit log created: event=%s actor=%s work_record=%s state=%s→%s',
            event_type,
            actor.email if actor else 'SYSTEM',
            work_record.id if work_record else 'N/A',
            before_state or '-',
            after_state or '-',
        )

        return entry

    @staticmethod
    def log_state_transition(
        work_record,
        before_state: str,
        after_state: str,
        event_type: str = None,
        metadata: dict = None,
    ) -> AuditLog:
        """
        Convenience method for logging state machine transitions.

        Auto-determines the event type from the after_state if not provided.
        """
        # Map states to event types
        state_event_map = {
            'WORK_SUBMITTED': AuditEventType.TIMESHEET_SUBMITTED,
            'WORK_APPROVED': AuditEventType.TIMESHEET_APPROVED,
            'WORK_REJECTED': AuditEventType.TIMESHEET_REJECTED,
            'INVOICE_GENERATED': AuditEventType.INVOICE_GENERATED,
            'INVOICE_APPROVED': AuditEventType.INVOICE_APPROVED,
            'PAYMENT_PENDING': AuditEventType.PAYMENT_INITIATED,
            'PAYMENT_RECEIVED': AuditEventType.PAYMENT_RECEIVED,
            'PAYROLL_PROCESSING': AuditEventType.PAYROLL_STARTED,
            'PAYROLL_COMPLETED': AuditEventType.PAYROLL_COMPLETED,
            'COMPLIANCE_SUBMITTED': AuditEventType.RTI_SUBMISSION_SENT,
            'COMPLETED': AuditEventType.PAYROLL_COMPLETED,
        }

        if not event_type:
            event_type = state_event_map.get(
                after_state, AuditEventType.CONFIG_CHANGED
            )

        return AuditService.log(
            event_type=event_type,
            work_record=work_record,
            organisation=work_record.umbrella,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata or {},
        )
