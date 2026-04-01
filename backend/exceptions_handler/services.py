"""
Exception Service — Module 7

Provides workflow operations for exception management:
raise, assign, review, escalate, resolve.

Every state change is audit-logged and triggers notifications.
"""

import logging
from django.utils import timezone
from django.db import transaction

from exceptions_handler.models import PlatformException, ExceptionComment
from core.enums import (
    ExceptionStatus,
    ExceptionSeverity,
    ExceptionType,
    AuditEventType,
)
from audit.services import AuditService
from notifications.services import NotificationDispatcher

logger = logging.getLogger('exceptions_handler')


class ExceptionService:
    """
    Centralised exception management service.

    Usage:
        from exceptions_handler.services import ExceptionService

        exc = ExceptionService.raise_exception(
            exception_type=ExceptionType.PAYMENT_MISMATCH,
            title='Payment amount mismatch',
            description='Expected £5000.00, received £4999.50',
            work_record=work_record,
            severity=ExceptionSeverity.HIGH,
            context_data={'expected': '5000.00', 'actual': '4999.50'},
        )
    """

    @staticmethod
    @transaction.atomic
    def raise_exception(
        exception_type: str,
        title: str,
        description: str,
        work_record=None,
        organisation=None,
        severity: str = ExceptionSeverity.MEDIUM,
        raised_by=None,
        context_data: dict = None,
    ) -> PlatformException:
        """
        Raise a new platform exception.

        This will:
        1. Create the exception record
        2. Log to audit trail
        3. Send notifications to relevant admins
        """
        exc = PlatformException.objects.create(
            exception_type=exception_type,
            title=title,
            description=description,
            work_record=work_record,
            organisation=organisation or (work_record.umbrella if work_record else None),
            severity=severity,
            status=ExceptionStatus.RAISED,
            raised_by=raised_by,
            context_data=context_data or {},
        )

        # Audit log
        AuditService.log(
            event_type=AuditEventType.EXCEPTION_RAISED,
            work_record=work_record,
            organisation=exc.organisation,
            after_state=ExceptionStatus.RAISED,
            metadata={
                'exception_id': str(exc.id),
                'exception_type': exception_type,
                'severity': severity,
                'title': title,
                'description': description,
            },
        )

        # Notify relevant admins
        NotificationDispatcher.dispatch(
            event_type=AuditEventType.EXCEPTION_RAISED,
            work_record=work_record,
            context={'description': description},
        )

        logger.warning(
            'Exception raised: %s [%s] — %s',
            title, severity, exception_type,
        )

        return exc

    @staticmethod
    @transaction.atomic
    def assign(exception_id, assigned_to_user) -> PlatformException:
        """Assign an exception to an admin for review."""
        exc = PlatformException.objects.select_for_update().get(id=exception_id)

        if exc.status == ExceptionStatus.RESOLVED:
            raise ValueError('Cannot assign a resolved exception.')

        old_status = exc.status
        exc.status = ExceptionStatus.ASSIGNED
        exc.assigned_to = assigned_to_user
        exc.assigned_at = timezone.now()
        exc.save(update_fields=['status', 'assigned_to', 'assigned_at', 'updated_at'])

        AuditService.log(
            event_type=AuditEventType.EXCEPTION_ASSIGNED,
            work_record=exc.work_record,
            organisation=exc.organisation,
            before_state=old_status,
            after_state=ExceptionStatus.ASSIGNED,
            metadata={
                'exception_id': str(exc.id),
                'assigned_to': assigned_to_user.email,
            },
        )

        logger.info('Exception %s assigned to %s', exc.id, assigned_to_user.email)
        return exc

    @staticmethod
    @transaction.atomic
    def start_review(exception_id) -> PlatformException:
        """Move exception to IN_REVIEW status."""
        exc = PlatformException.objects.select_for_update().get(id=exception_id)

        if exc.status not in [ExceptionStatus.ASSIGNED, ExceptionStatus.ESCALATED]:
            raise ValueError(
                f'Cannot start review from status {exc.status}. '
                f'Must be ASSIGNED or ESCALATED.'
            )

        old_status = exc.status
        exc.status = ExceptionStatus.IN_REVIEW
        exc.save(update_fields=['status', 'updated_at'])

        AuditService.log(
            event_type=AuditEventType.EXCEPTION_ASSIGNED,
            work_record=exc.work_record,
            organisation=exc.organisation,
            before_state=old_status,
            after_state=ExceptionStatus.IN_REVIEW,
            metadata={'exception_id': str(exc.id)},
        )

        return exc

    @staticmethod
    @transaction.atomic
    def escalate(exception_id, reason: str) -> PlatformException:
        """Escalate an exception to a higher authority."""
        exc = PlatformException.objects.select_for_update().get(id=exception_id)

        if exc.status not in [ExceptionStatus.IN_REVIEW, ExceptionStatus.ASSIGNED]:
            raise ValueError(f'Cannot escalate from status {exc.status}.')

        old_status = exc.status
        exc.status = ExceptionStatus.ESCALATED
        exc.severity = ExceptionSeverity.CRITICAL  # Auto-escalate severity
        exc.save(update_fields=['status', 'severity', 'updated_at'])

        # Add escalation comment
        ExceptionComment.objects.create(
            exception=exc,
            author=exc.assigned_to or exc.raised_by,
            message=f'ESCALATED: {reason}',
        )

        AuditService.log(
            event_type=AuditEventType.EXCEPTION_ESCALATED,
            work_record=exc.work_record,
            organisation=exc.organisation,
            before_state=old_status,
            after_state=ExceptionStatus.ESCALATED,
            metadata={
                'exception_id': str(exc.id),
                'escalation_reason': reason,
            },
        )

        logger.warning('Exception %s escalated: %s', exc.id, reason)
        return exc

    @staticmethod
    @transaction.atomic
    def resolve(
        exception_id,
        resolution_notes: str,
        justification: str = '',
        is_override: bool = False,
    ) -> PlatformException:
        """
        Resolve an exception.

        If is_override=True, justification is MANDATORY.
        Resolution is logged immutably in the audit trail.
        """
        exc = PlatformException.objects.select_for_update().get(id=exception_id)

        if exc.status == ExceptionStatus.RESOLVED:
            raise ValueError('Exception is already resolved.')

        # Mandatory justification for overrides
        if is_override and not justification.strip():
            raise ValueError(
                'Manual overrides require a mandatory written justification. '
                'This is a compliance requirement.'
            )

        old_status = exc.status
        exc.status = ExceptionStatus.RESOLVED
        exc.resolution_notes = resolution_notes
        exc.justification = justification
        exc.is_override = is_override
        exc.resolved_at = timezone.now()
        exc.save(update_fields=[
            'status', 'resolution_notes', 'justification',
            'is_override', 'resolved_at', 'updated_at',
        ])

        # Audit log — resolution details stored immutably
        event_type = (
            AuditEventType.MANUAL_OVERRIDE if is_override
            else AuditEventType.EXCEPTION_RESOLVED
        )
        AuditService.log(
            event_type=event_type,
            work_record=exc.work_record,
            organisation=exc.organisation,
            before_state=old_status,
            after_state=ExceptionStatus.RESOLVED,
            metadata={
                'exception_id': str(exc.id),
                'resolution_notes': resolution_notes,
                'justification': justification,
                'is_override': is_override,
                'sla_hours': round(exc.sla_hours_elapsed, 2),
            },
        )

        # Notify stakeholders
        NotificationDispatcher.dispatch(
            event_type=AuditEventType.EXCEPTION_RESOLVED,
            work_record=exc.work_record,
        )

        logger.info(
            'Exception %s resolved (override=%s, SLA=%.1fh)',
            exc.id, is_override, exc.sla_hours_elapsed,
        )

        return exc

    @staticmethod
    def check_blocking_exceptions(work_record) -> list:
        """
        Check if a work record has any unresolved exceptions
        that block workflow progression.

        Returns list of blocking exceptions (empty if none).
        """
        return list(
            PlatformException.objects.filter(
                work_record=work_record,
            ).exclude(
                status=ExceptionStatus.RESOLVED,
            )
        )

    @staticmethod
    def add_comment(exception_id, author, message: str) -> ExceptionComment:
        """Add a comment to an exception thread."""
        exc = PlatformException.objects.get(id=exception_id)
        comment = ExceptionComment.objects.create(
            exception=exc,
            author=author,
            message=message,
        )
        logger.info('Comment added to exception %s by %s', exc.id, author.email)
        return comment
