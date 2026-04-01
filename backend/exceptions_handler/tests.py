"""Tests for Module 7 — Exception Handling."""

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date

from exceptions_handler.models import PlatformException
from exceptions_handler.services import ExceptionService
from core.models import User, Organisation, WorkRecord
from core.enums import (
    UserRole,
    OrganisationType,
    ExceptionType,
    ExceptionSeverity,
    ExceptionStatus,
    WorkRecordState,
)


class ExceptionServiceTest(TestCase):
    """Test the ExceptionService."""

    def setUp(self):
        self.agency = Organisation.objects.create(
            name='Test Agency', org_type=OrganisationType.AGENCY,
        )
        self.umbrella = Organisation.objects.create(
            name='Test Umbrella', org_type=OrganisationType.UMBRELLA,
            paye_reference='123/AB45678',
        )
        self.admin = User.objects.create_user(
            email='admin@test.com', username='admin',
            password='testpass123', role=UserRole.UMBRELLA_ADMIN,
        )
        self.contractor = User.objects.create_user(
            email='contractor@test.com', username='contractor',
            password='testpass123', role=UserRole.CONTRACTOR,
        )
        self.work_record = WorkRecord.objects.create(
            contractor=self.contractor,
            agency=self.agency, umbrella=self.umbrella,
            state=WorkRecordState.PAYMENT_PENDING,
            period_start=date(2025, 6, 1), period_end=date(2025, 6, 7),
            hours_worked=Decimal('40.00'), hourly_rate=Decimal('25.00'),
            gross_amount=Decimal('1000.00'),
        )

    def test_raise_exception(self):
        """Test raising a platform exception."""
        exc = ExceptionService.raise_exception(
            exception_type=ExceptionType.PAYMENT_MISMATCH,
            title='Payment mismatch',
            description='Expected £1000, received £999',
            work_record=self.work_record,
            severity=ExceptionSeverity.HIGH,
        )
        self.assertEqual(exc.status, ExceptionStatus.RAISED)
        self.assertEqual(exc.exception_type, ExceptionType.PAYMENT_MISMATCH)
        self.assertTrue(exc.is_blocking)

    def test_assign_exception(self):
        """Test assigning an exception."""
        exc = ExceptionService.raise_exception(
            exception_type=ExceptionType.GENERAL,
            title='Test', description='Test',
        )
        exc = ExceptionService.assign(exc.id, self.admin)
        self.assertEqual(exc.status, ExceptionStatus.ASSIGNED)
        self.assertEqual(exc.assigned_to, self.admin)

    def test_resolve_exception(self):
        """Test resolving an exception."""
        exc = ExceptionService.raise_exception(
            exception_type=ExceptionType.GENERAL,
            title='Test', description='Test',
        )
        exc = ExceptionService.resolve(
            exc.id,
            resolution_notes='Fixed the issue.',
        )
        self.assertEqual(exc.status, ExceptionStatus.RESOLVED)
        self.assertFalse(exc.is_blocking)

    def test_override_requires_justification(self):
        """Test that manual overrides require justification."""
        exc = ExceptionService.raise_exception(
            exception_type=ExceptionType.GENERAL,
            title='Test', description='Test',
        )
        with self.assertRaises(ValueError):
            ExceptionService.resolve(
                exc.id,
                resolution_notes='Override',
                is_override=True,
                justification='',  # Empty — should fail
            )

    def test_override_with_justification_succeeds(self):
        """Test that manual override with justification works."""
        exc = ExceptionService.raise_exception(
            exception_type=ExceptionType.GENERAL,
            title='Test', description='Test',
        )
        exc = ExceptionService.resolve(
            exc.id,
            resolution_notes='Manually overriding',
            is_override=True,
            justification='Rounding difference of £0.01, acceptable per policy.',
        )
        self.assertTrue(exc.is_override)
        self.assertIn('Rounding difference', exc.justification)

    def test_blocking_exceptions_check(self):
        """Test checking for blocking exceptions."""
        ExceptionService.raise_exception(
            exception_type=ExceptionType.PAYMENT_MISMATCH,
            title='Block test', description='Test',
            work_record=self.work_record,
        )
        blocking = ExceptionService.check_blocking_exceptions(self.work_record)
        self.assertEqual(len(blocking), 1)

    def test_resolved_exceptions_dont_block(self):
        """Test that resolved exceptions don't block."""
        exc = ExceptionService.raise_exception(
            exception_type=ExceptionType.GENERAL,
            title='Test', description='Test',
            work_record=self.work_record,
        )
        ExceptionService.resolve(exc.id, resolution_notes='Done')
        blocking = ExceptionService.check_blocking_exceptions(self.work_record)
        self.assertEqual(len(blocking), 0)
