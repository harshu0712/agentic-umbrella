"""
Audit Signals — automatic logging of model state changes.

Listens to post_save signals on core models and automatically
creates audit log entries for state transitions.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import WorkRecord
from audit.services import AuditService
from core.enums import AuditEventType


@receiver(post_save, sender=WorkRecord)
def log_work_record_state_change(sender, instance, created, **kwargs):
    """
    Auto-log work record state changes.

    On creation, logs the initial state.
    On update, attempts to detect state changes and log transitions.
    """
    if created:
        AuditService.log(
            event_type=AuditEventType.TIMESHEET_SUBMITTED,
            work_record=instance,
            organisation=instance.umbrella,
            after_state=instance.state,
            metadata={
                'contractor': str(instance.contractor_id),
                'agency': str(instance.agency_id),
                'hours_worked': str(instance.hours_worked),
                'gross_amount': str(instance.gross_amount),
                'period': f"{instance.period_start} to {instance.period_end}",
            },
        )
