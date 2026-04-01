"""
Notification Models — Module 7

Event-driven notification system. Every major state transition
triggers notifications to relevant stakeholders.
"""

import uuid
from django.db import models
from django.conf import settings

from core.enums import NotificationChannel, NotificationStatus


class Notification(models.Model):
    """
    A notification sent to a user about a platform event.

    Notifications are:
    - Logged: every notification is recorded in the audit trail
    - Non-blocking: notification failures do not block the workflow
    - Multi-channel: delivered via email and/or in-app
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )

    # Event context
    event_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text='The audit event type that triggered this notification.',
    )
    work_record = models.ForeignKey(
        'core.WorkRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text='URL the user should navigate to for action.',
    )

    # Delivery
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error details if delivery failed.',
    )

    # Read tracking (for in-app notifications)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['event_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"[{self.channel}] {self.title} → {self.recipient.email}"


class NotificationPreference(models.Model):
    """
    Per-user notification channel preferences.

    Users can opt in/out of email notifications for specific event types.
    In-app notifications are always enabled and cannot be disabled.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    event_type = models.CharField(
        max_length=50,
        help_text='The event type this preference applies to.',
    )
    email_enabled = models.BooleanField(
        default=True,
        help_text='Whether to send email notifications for this event type.',
    )
    in_app_enabled = models.BooleanField(
        default=True,
        help_text='Whether to show in-app notifications. Always true by default.',
    )

    class Meta:
        db_table = 'notifications_preference'
        unique_together = ['user', 'event_type']

    def __str__(self):
        return f"{self.user.email} | {self.event_type} | email={self.email_enabled}"
