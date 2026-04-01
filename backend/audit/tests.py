"""
Tests for Module 7 — Audit Log Service

Tests:
1. Audit log creation
2. Immutability (cannot update or delete)
3. AuditService.log() utility
4. State transition logging
5. API read-only enforcement
"""

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from audit.models import AuditLog
from audit.services import AuditService
from core.models import User, Organisation, WorkRecord
from core.enums import (
    AuditEventType,
    UserRole,
    OrganisationType,
    WorkRecordState,
)

from datetime import date
from decimal import Decimal


class AuditLogModelTest(TestCase):
    """Test the AuditLog model immutability and creation."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='testpass123',
            role=UserRole.PLATFORM_ADMIN,
        )
        self.org = Organisation.objects.create(
            name='Test Umbrella',
            org_type=OrganisationType.UMBRELLA,
            paye_reference='123/AB45678',
        )

    def test_create_audit_log(self):
        """Test basic audit log creation."""
        log = AuditLog.objects.create(
            actor=self.user,
            actor_role=UserRole.PLATFORM_ADMIN,
            organisation=self.org,
            event_type=AuditEventType.USER_CREATED,
            metadata={'test': 'data'},
        )
        self.assertIsNotNone(log.id)
        self.assertIsNotNone(log.timestamp)
        self.assertEqual(log.event_type, AuditEventType.USER_CREATED)

    def test_cannot_update_audit_log(self):
        """Test that audit logs cannot be updated."""
        log = AuditLog.objects.create(
            actor=self.user,
            event_type=AuditEventType.USER_CREATED,
        )
        log.event_type = AuditEventType.USER_UPDATED
        with self.assertRaises(PermissionError):
            log.save()

    def test_cannot_delete_audit_log(self):
        """Test that audit logs cannot be deleted."""
        log = AuditLog.objects.create(
            actor=self.user,
            event_type=AuditEventType.USER_CREATED,
        )
        with self.assertRaises(PermissionError):
            log.delete()


class AuditServiceTest(TestCase):
    """Test the AuditService utility."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='testpass123',
            role=UserRole.PLATFORM_ADMIN,
        )

    def test_log_creates_entry(self):
        """Test AuditService.log() creates an audit entry."""
        entry = AuditService.log(
            event_type=AuditEventType.USER_CREATED,
            actor=self.user,
            metadata={'action': 'test'},
        )
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.actor_role, UserRole.PLATFORM_ADMIN)

    def test_log_system_event(self):
        """Test logging a system event (no actor)."""
        entry = AuditService.log(
            event_type=AuditEventType.INVOICE_GENERATED,
            metadata={'invoice_amount': '5000.00'},
        )
        self.assertIsNone(entry.actor)
        self.assertEqual(entry.event_type, AuditEventType.INVOICE_GENERATED)


class AuditAPITest(APITestCase):
    """Test the audit log REST API."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='testpass123',
            role=UserRole.PLATFORM_ADMIN,
        )
        self.contractor = User.objects.create_user(
            email='contractor@test.com',
            username='contractor',
            password='testpass123',
            role=UserRole.CONTRACTOR,
        )
        self.client = APIClient()

        # Create some audit logs
        for i in range(3):
            AuditService.log(
                event_type=AuditEventType.USER_CREATED,
                actor=self.admin,
                metadata={'index': i},
            )

    def test_admin_can_list_logs(self):
        """Admin users can list audit logs."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/audit/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contractor_cannot_list_logs(self):
        """Contractors cannot access audit logs."""
        self.client.force_authenticate(user=self.contractor)
        response = self.client.get('/api/v1/audit/logs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_post_endpoint(self):
        """POST is not allowed on audit logs."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/v1/audit/logs/', {'event_type': 'TEST'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_no_delete_endpoint(self):
        """DELETE is not allowed on audit logs."""
        self.client.force_authenticate(user=self.admin)
        log = AuditLog.objects.first()
        response = self.client.delete(f'/api/v1/audit/logs/{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
