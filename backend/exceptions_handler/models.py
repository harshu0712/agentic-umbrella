"""
Exception Handling Models — Module 7

Platform exceptions are raised when the system encounters a state
it cannot automatically resolve. All exceptions block workflow
progression until resolved.
"""

import uuid
from django.db import models
from django.conf import settings

from core.enums import ExceptionSeverity, ExceptionStatus, ExceptionType


class PlatformException(models.Model):
    """
    A platform exception that blocks workflow progression.

    Exceptions follow this lifecycle:
    RAISED → ASSIGNED → IN_REVIEW → RESOLVED
                                  → ESCALATED → IN_REVIEW → RESOLVED

    Manual overrides require a mandatory justification stored immutably.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Classification
    exception_type = models.CharField(
        max_length=50,
        choices=ExceptionType.choices,
        db_index=True,
    )
    severity = models.CharField(
        max_length=20,
        choices=ExceptionSeverity.choices,
        default=ExceptionSeverity.MEDIUM,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(
        help_text='Detailed description of the exception.',
    )

    # Context
    work_record = models.ForeignKey(
        'core.WorkRecord',
        on_delete=models.PROTECT,
        related_name='exceptions',
        null=True,
        blank=True,
    )
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.PROTECT,
        related_name='exceptions',
        null=True,
        blank=True,
    )

    # Lifecycle
    status = models.CharField(
        max_length=20,
        choices=ExceptionStatus.choices,
        default=ExceptionStatus.RAISED,
        db_index=True,
    )
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='exceptions_raised',
        null=True,
        blank=True,
        help_text='User or system that raised the exception. Null for system-raised.',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='exceptions_assigned',
        null=True,
        blank=True,
    )

    # Resolution
    resolution_notes = models.TextField(
        blank=True,
        help_text='Notes about how the exception was resolved.',
    )
    justification = models.TextField(
        blank=True,
        help_text=(
            'Mandatory justification for manual overrides. '
            'Stored immutably in the audit log.'
        ),
    )
    is_override = models.BooleanField(
        default=False,
        help_text='Whether this exception was resolved via manual override.',
    )

    # Metadata
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context data (e.g., expected vs actual amounts).',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'exceptions_platform_exception'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['exception_type']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['work_record', 'status']),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title} ({self.get_status_display()})"

    @property
    def is_resolved(self):
        return self.status == ExceptionStatus.RESOLVED

    @property
    def is_blocking(self):
        """An exception is blocking if it's not resolved."""
        return self.status != ExceptionStatus.RESOLVED

    @property
    def sla_hours_elapsed(self):
        """Hours since the exception was raised."""
        from django.utils import timezone
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
        else:
            delta = timezone.now() - self.created_at
        return delta.total_seconds() / 3600


class ExceptionComment(models.Model):
    """
    Threaded comments on an exception.

    Provides a discussion trail for the resolution process.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exception = models.ForeignKey(
        PlatformException,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='exception_comments',
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exceptions_comment'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.exception.title}"
