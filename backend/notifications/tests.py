"""Tests for Notification Service — Module 7."""

from django.test import TestCase
from core.models import User
from core.enums import UserRole
from notifications.models import Notification


class NotificationModelTest(TestCase):
    """Test notification model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com', username='user',
            password='testpass123', role=UserRole.CONTRACTOR,
        )

    def test_create_notification(self):
        notif = Notification.objects.create(
            recipient=self.user,
            event_type='TIMESHEET_APPROVED',
            title='Your timesheet was approved',
            message='Details here...',
            channel='IN_APP',
            status='SENT',
        )
        self.assertIsNotNone(notif.id)
        self.assertFalse(notif.is_read)

    def test_mark_as_read(self):
        from django.utils import timezone
        notif = Notification.objects.create(
            recipient=self.user,
            event_type='TEST',
            title='Test',
            message='Test message',
            channel='IN_APP',
            status='SENT',
        )
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)
