"""
Notification Dispatcher Service — Module 7

Event-driven service that:
1. Looks up the notification matrix for recipient roles
2. Finds actual users with those roles (scoped to relevant orgs)
3. Creates in-app notifications
4. Sends email notifications
5. Logs everything to the audit trail

All notification failures are non-blocking — they never halt the workflow.
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from notifications.models import Notification, NotificationPreference
from notifications.matrix import NOTIFICATION_MATRIX, NOTIFICATION_MESSAGES
from core.enums import (
    NotificationChannel,
    NotificationStatus,
    AuditEventType,
)
from core.models import User, Membership

logger = logging.getLogger('notifications')


class NotificationDispatcher:
    """
    Central notification service.

    Usage:
        from notifications.services import NotificationDispatcher

        NotificationDispatcher.dispatch(
            event_type=AuditEventType.TIMESHEET_APPROVED,
            work_record=work_record,
            context={'period_start': '2025-01-01', 'period_end': '2025-01-07'}
        )
    """

    @staticmethod
    def dispatch(
        event_type: str,
        work_record=None,
        context: dict = None,
        specific_recipients: list = None,
    ):
        """
        Dispatch notifications for an event.

        Args:
            event_type: The audit event type that triggered this notification.
            work_record: The work record this relates to (used for org scoping).
            context: Template variables for the message (e.g., amounts, dates).
            specific_recipients: If provided, override the matrix and notify
                                 these specific users instead.
        """
        context = context or {}
        notifications_created = []

        try:
            # Determine recipients
            if specific_recipients:
                recipients = specific_recipients
            else:
                recipients = NotificationDispatcher._resolve_recipients(
                    event_type, work_record
                )

            if not recipients:
                logger.info(
                    'No recipients found for event %s', event_type
                )
                return notifications_created

            # Get message template
            message_config = NOTIFICATION_MESSAGES.get(event_type, {})
            title = message_config.get('title', f'Platform Notification: {event_type}')
            message_template = message_config.get('message', f'Event: {event_type}')

            # Format message with context
            try:
                message = message_template.format(**context)
            except (KeyError, IndexError):
                message = message_template  # Use template as-is if formatting fails

            # Create notifications for each recipient
            for recipient in recipients:
                # In-app notification (always created)
                in_app = NotificationDispatcher._create_in_app(
                    recipient=recipient,
                    event_type=event_type,
                    title=title,
                    message=message,
                    work_record=work_record,
                )
                notifications_created.append(in_app)

                # Email notification (if user hasn't disabled it)
                if NotificationDispatcher._should_send_email(recipient, event_type):
                    email_notif = NotificationDispatcher._send_email(
                        recipient=recipient,
                        event_type=event_type,
                        title=title,
                        message=message,
                        work_record=work_record,
                    )
                    notifications_created.append(email_notif)

            logger.info(
                'Dispatched %d notifications for event %s',
                len(notifications_created), event_type
            )

        except Exception as e:
            # Non-blocking — log error but don't raise
            logger.error(
                'Failed to dispatch notifications for event %s: %s',
                event_type, str(e),
                exc_info=True,
            )

        return notifications_created

    @staticmethod
    def _resolve_recipients(event_type, work_record):
        """
        Resolve the actual User objects that should receive this notification.

        Uses the notification matrix to determine roles, then finds users
        with those roles in the relevant organisations.
        """
        target_roles = NOTIFICATION_MATRIX.get(event_type, [])
        if not target_roles:
            return []

        recipients = set()

        for role in target_roles:
            if role == 'CONTRACTOR' and work_record:
                # Contractors are directly linked to work records
                recipients.add(work_record.contractor)
            elif work_record:
                # Find users with this role in the relevant orgs
                org_ids = [work_record.agency_id, work_record.umbrella_id]
                memberships = Membership.objects.filter(
                    role=role,
                    organisation_id__in=org_ids,
                    is_active=True,
                ).select_related('user')
                for membership in memberships:
                    if membership.user.is_active:
                        recipients.add(membership.user)
            else:
                # No work record context — notify all users with this role
                users = User.objects.filter(
                    role=role,
                    is_active=True,
                )
                recipients.update(users)

        return list(recipients)

    @staticmethod
    def _create_in_app(recipient, event_type, title, message, work_record=None):
        """Create an in-app notification."""
        return Notification.objects.create(
            recipient=recipient,
            event_type=event_type,
            title=title,
            message=message,
            work_record=work_record,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.SENT,
            sent_at=timezone.now(),
        )

    @staticmethod
    def _send_email(recipient, event_type, title, message, work_record=None):
        """Send an email notification."""
        notification = Notification.objects.create(
            recipient=recipient,
            event_type=event_type,
            title=title,
            message=message,
            work_record=work_record,
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.PENDING,
        )

        try:
            send_mail(
                subject=f'[Agentic Umbrella] {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            notification.status = NotificationStatus.SENT
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at'])

            logger.info('Email sent to %s for event %s', recipient.email, event_type)

        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            notification.save(update_fields=['status', 'error_message'])

            logger.error(
                'Failed to send email to %s: %s',
                recipient.email, str(e)
            )

        return notification

    @staticmethod
    def _should_send_email(user, event_type):
        """Check if a user has email enabled for this event type."""
        pref = NotificationPreference.objects.filter(
            user=user,
            event_type=event_type,
        ).first()

        # Default: email enabled
        if pref is None:
            return True
        return pref.email_enabled
