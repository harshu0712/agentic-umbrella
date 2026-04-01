"""
Audit Log Model — Module 7

Append-only, immutable audit trail for every platform action.
This is a legal requirement for UK umbrella companies.

Design decisions:
- No updated_at field (immutable records)
- No soft delete (records cannot be deleted)
- JSONField for flexible metadata storage
- Indexed on timestamp, actor, event_type, work_record for fast queries
- Cursor-based pagination for consistent large dataset traversal
"""

import uuid
from django.db import models
from django.conf import settings

from core.enums import AuditEventType


class AuditLog(models.Model):
    """
    Immutable audit log entry.

    Every state transition, approval, rejection, login, configuration change,
    and financial action creates one of these records. They cannot be modified
    or deleted after creation.

    This table is the platform's legal compliance backbone.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Who performed the action
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_logs',
        null=True,
        blank=True,
        help_text='User who performed the action. Null for system-initiated events.',
    )
    actor_role = models.CharField(
        max_length=30,
        blank=True,
        help_text='Role of the actor at the time of the action.',
    )

    # Where the action occurred
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.PROTECT,
        related_name='audit_logs',
        null=True,
        blank=True,
        help_text='Organisation context of the action.',
    )

    # What happened
    event_type = models.CharField(
        max_length=50,
        choices=AuditEventType.choices,
        db_index=True,
        help_text='Categorised event type.',
    )

    # Which work record this relates to
    work_record = models.ForeignKey(
        'core.WorkRecord',
        on_delete=models.PROTECT,
        related_name='audit_logs',
        null=True,
        blank=True,
        help_text='The Work Record this event relates to, if applicable.',
    )

    # State transition tracking
    before_state = models.CharField(
        max_length=30,
        blank=True,
        help_text='State before the transition.',
    )
    after_state = models.CharField(
        max_length=30,
        blank=True,
        help_text='State after the transition.',
    )

    # Flexible metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Additional context: rejection reasons, amounts, IP addresses, '
            'override justifications, etc.'
        ),
    )

    # Request context (populated by middleware)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the request.',
    )
    user_agent = models.TextField(
        blank=True,
        help_text='User agent string of the request.',
    )
    request_id = models.CharField(
        max_length=64,
        blank=True,
        help_text='Unique request identifier for tracing.',
    )

    class Meta:
        db_table = 'audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['actor', '-timestamp']),
            models.Index(fields=['work_record', '-timestamp']),
            models.Index(fields=['organisation', '-timestamp']),
            models.Index(fields=['request_id']),
        ]
        # Prevent Django admin from offering delete
        default_permissions = ('add', 'view')

    def __str__(self):
        actor_name = self.actor.email if self.actor else 'SYSTEM'
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] "
            f"{self.event_type} by {actor_name}"
        )

    def save(self, *args, **kwargs):
        # Enforce immutability — only allow creation, not updates
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise PermissionError(
                "Audit log entries are immutable. "
                "Cannot update an existing audit record."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError(
            "Audit log entries cannot be deleted. "
            "This is a legal and compliance requirement."
        )
