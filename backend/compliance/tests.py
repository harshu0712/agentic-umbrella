"""
Tests for Module 6 — Compliance Engine

Tests:
1. Tax code validation
2. NI number validation
3. Pre-payroll compliance checks
4. Anomaly detection
5. Tax period calculations
"""

from django.test import TestCase
from decimal import Decimal
from datetime import date

from compliance.validators import validate_tax_code, validate_ni_number
from compliance.services.rti_generator import RTIGeneratorService
from compliance.constants import (
    PERSONAL_ALLOWANCE,
    STANDARD_TAX_CODE,
)
from core.models import User, Organisation, WorkRecord, ContractorLink
from core.enums import (
    UserRole,
    OrganisationType,
    WorkRecordState,
)


class TaxCodeValidationTest(TestCase):
    """Test UK tax code validation."""

    def test_standard_code_1257L(self):
        result = validate_tax_code('1257L')
        self.assertTrue(result['valid'])
        self.assertEqual(result['parsed']['type'], 'standard')
        self.assertEqual(result['parsed']['allowance'], 12570)

    def test_standard_code_1100L(self):
        result = validate_tax_code('1100L')
        self.assertTrue(result['valid'])

    def test_special_code_BR(self):
        result = validate_tax_code('BR')
        self.assertTrue(result['valid'])
        self.assertEqual(result['parsed']['type'], 'special')

    def test_special_code_D0(self):
        result = validate_tax_code('D0')
        self.assertTrue(result['valid'])

    def test_special_code_NT(self):
        result = validate_tax_code('NT')
        self.assertTrue(result['valid'])

    def test_k_code(self):
        result = validate_tax_code('K500')
        self.assertTrue(result['valid'])
        self.assertEqual(result['parsed']['type'], 'K')
        self.assertEqual(result['parsed']['allowance'], -5000)

    def test_scottish_code(self):
        result = validate_tax_code('S1257L')
        self.assertTrue(result['valid'])
        self.assertEqual(result['parsed']['country_prefix'], 'S')

    def test_welsh_code(self):
        result = validate_tax_code('C1257L')
        self.assertTrue(result['valid'])
        self.assertEqual(result['parsed']['country_prefix'], 'C')

    def test_week1_month1(self):
        result = validate_tax_code('1257L W1')
        self.assertTrue(result['valid'])
        self.assertTrue(result['parsed']['week1_month1'])

    def test_empty_code(self):
        result = validate_tax_code('')
        self.assertFalse(result['valid'])

    def test_invalid_code(self):
        result = validate_tax_code('INVALID')
        self.assertFalse(result['valid'])


class NINumberValidationTest(TestCase):
    """Test UK National Insurance number validation."""

    def test_valid_ni_number(self):
        result = validate_ni_number('QQ123456C')
        self.assertTrue(result['valid'])

    def test_valid_ni_with_spaces(self):
        result = validate_ni_number('QQ 12 34 56 C')
        self.assertTrue(result['valid'])

    def test_empty_ni(self):
        result = validate_ni_number('')
        self.assertFalse(result['valid'])

    def test_invalid_format(self):
        result = validate_ni_number('12345')
        self.assertFalse(result['valid'])

    def test_excluded_prefix_BG(self):
        result = validate_ni_number('BG123456A')
        self.assertFalse(result['valid'])

    def test_excluded_prefix_GB(self):
        result = validate_ni_number('GB123456A')
        self.assertFalse(result['valid'])

    def test_invalid_second_letter(self):
        result = validate_ni_number('QD123456A')
        self.assertFalse(result['valid'])


class TaxPeriodCalculationTest(TestCase):
    """Test tax year and period determination."""

    def test_april_is_period_1(self):
        tax_year, period = RTIGeneratorService._get_tax_period(date(2025, 4, 15))
        self.assertEqual(tax_year, '2025-26')
        self.assertEqual(period, 1)

    def test_march_is_period_12(self):
        tax_year, period = RTIGeneratorService._get_tax_period(date(2026, 3, 15))
        self.assertEqual(tax_year, '2025-26')
        self.assertEqual(period, 12)

    def test_january_is_period_10(self):
        tax_year, period = RTIGeneratorService._get_tax_period(date(2026, 1, 15))
        self.assertEqual(tax_year, '2025-26')
        self.assertEqual(period, 10)

    def test_july_is_period_4(self):
        tax_year, period = RTIGeneratorService._get_tax_period(date(2025, 7, 15))
        self.assertEqual(tax_year, '2025-26')
        self.assertEqual(period, 4)


class ComplianceValidationTest(TestCase):
    """Test pre-payroll compliance validation."""

    def setUp(self):
        self.agency = Organisation.objects.create(
            name='Test Agency',
            org_type=OrganisationType.AGENCY,
        )
        self.umbrella = Organisation.objects.create(
            name='Test Umbrella',
            org_type=OrganisationType.UMBRELLA,
            paye_reference='123/AB45678',
            paye_scheme_active=True,
        )
        self.contractor = User.objects.create_user(
            email='contractor@test.com',
            username='contractor',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            role=UserRole.CONTRACTOR,
        )
        self.contractor_link = ContractorLink.objects.create(
            user=self.contractor,
            agency=self.agency,
            umbrella=self.umbrella,
            hourly_rate=Decimal('25.00'),
            tax_code='1257L',
            ni_number='QQ123456C',
            start_date=date(2025, 1, 1),
        )
        self.work_record = WorkRecord.objects.create(
            contractor=self.contractor,
            agency=self.agency,
            umbrella=self.umbrella,
            state=WorkRecordState.PAYMENT_RECEIVED,
            period_start=date(2025, 6, 1),
            period_end=date(2025, 6, 7),
            hours_worked=Decimal('40.00'),
            hourly_rate=Decimal('25.00'),
            gross_amount=Decimal('1000.00'),
        )

    def test_all_checks_pass(self):
        """Test that a fully compliant work record passes all checks."""
        from compliance.services import ComplianceValidationService
        check = ComplianceValidationService.validate(self.work_record)
        self.assertTrue(check.all_passed)
        self.assertEqual(check.failed_checks_count, 0)

    def test_missing_tax_code_fails(self):
        """Test that missing tax code fails validation."""
        self.contractor_link.tax_code = ''
        self.contractor_link.save()

        from compliance.services import ComplianceValidationService
        check = ComplianceValidationService.validate(self.work_record)
        self.assertFalse(check.all_passed)

        failed = [c for c in check.checks if not c['passed']]
        check_names = [c['check'] for c in failed]
        self.assertIn('tax_code_valid', check_names)

    def test_inactive_paye_scheme_fails(self):
        """Test that inactive PAYE scheme fails validation."""
        self.umbrella.paye_scheme_active = False
        self.umbrella.save()

        from compliance.services import ComplianceValidationService
        check = ComplianceValidationService.validate(self.work_record)
        self.assertFalse(check.all_passed)

    def test_wrong_state_fails(self):
        """Test that wrong work record state fails validation."""
        self.work_record.state = WorkRecordState.INVOICE_APPROVED
        self.work_record.save()

        from compliance.services import ComplianceValidationService
        check = ComplianceValidationService.validate(self.work_record)
        self.assertFalse(check.all_passed)

    def test_below_minimum_wage_fails(self):
        """Test that below minimum wage rate fails."""
        self.work_record.hourly_rate = Decimal('5.00')
        self.work_record.save()

        from compliance.services import ComplianceValidationService
        check = ComplianceValidationService.validate(self.work_record)
        self.assertFalse(check.all_passed)
