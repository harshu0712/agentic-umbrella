"""
Core models for the Agentic Umbrella Platform.

These are lightweight stub models that provide FK references for Module 6 and 7.
In the full platform, these would be replaced by the complete implementations
from modules 1-5. They contain only the fields needed by compliance and audit.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from core.enums import (
    OrganisationType,
    UserRole,
    WorkRecordState,
    VALID_STATE_TRANSITIONS,
)


class User(AbstractUser):
    """
    Custom user model for the platform.

    Extends Django's AbstractUser with platform-specific fields.
    Serves as the identity for all actors (agency admins, contractors, etc.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.CONTRACTOR,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Use email for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'core_user'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def full_name(self):
        return self.get_full_name() or self.email


class Organisation(models.Model):
    """
    Represents an Agency or Umbrella Company on the platform.

    Multi-tenant entity — all data access must be scoped to organisation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    org_type = models.CharField(
        max_length=20,
        choices=OrganisationType.choices,
        db_index=True,
    )
    registration_number = models.CharField(max_length=50, blank=True)
    paye_reference = models.CharField(
        max_length=20,
        blank=True,
        help_text='HMRC PAYE scheme reference (e.g., 123/AB45678)',
    )
    paye_scheme_active = models.BooleanField(
        default=True,
        help_text='Whether the PAYE scheme is currently active with HMRC',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'core_organisation'
        ordering = ['name']
        indexes = [
            models.Index(fields=['org_type']),
            models.Index(fields=['paye_reference']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"


class Membership(models.Model):
    """
    Links a user to an organisation with a specific role.

    Enables multi-organisation membership — a user can belong to
    multiple organisations with different roles in each.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_membership'
        unique_together = ['user', 'organisation', 'role']
        indexes = [
            models.Index(fields=['user', 'organisation']),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.organisation.name} ({self.get_role_display()})"


class ContractorLink(models.Model):
    """
    Links a contractor to exactly one Agency AND one Umbrella Company.

    Contains contractor-specific employment details needed for payroll
    and compliance processing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='contractor_link',
        limit_choices_to={'role': UserRole.CONTRACTOR},
    )
    agency = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name='agency_contractors',
        limit_choices_to={'org_type': OrganisationType.AGENCY},
    )
    umbrella = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name='umbrella_contractors',
        limit_choices_to={'org_type': OrganisationType.UMBRELLA},
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Agreed hourly rate in GBP',
    )
    tax_code = models.CharField(
        max_length=10,
        blank=True,
        help_text='HMRC PAYE tax code (e.g., 1257L)',
    )
    ni_number = models.CharField(
        max_length=9,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$',
                message='Enter a valid UK National Insurance number (e.g., QQ123456C)',
            ),
        ],
        help_text='UK National Insurance number',
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_contractor_link'
        indexes = [
            models.Index(fields=['agency']),
            models.Index(fields=['umbrella']),
            models.Index(fields=['tax_code']),
        ]

    def __str__(self):
        return f"{self.user.email} ({self.agency.name} → {self.umbrella.name})"


class WorkRecord(models.Model):
    """
    Central entity tracking the full lifecycle of a contractor's work period.

    This is the entity that flows through the state machine from
    WORK_SUBMITTED all the way to COMPLETED. Every module operates
    on or references a WorkRecord.

    Implements optimistic locking via the `version` field to prevent
    concurrent modification conflicts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contractor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='work_records',
        limit_choices_to={'role': UserRole.CONTRACTOR},
    )
    agency = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name='agency_work_records',
        limit_choices_to={'org_type': OrganisationType.AGENCY},
    )
    umbrella = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name='umbrella_work_records',
        limit_choices_to={'org_type': OrganisationType.UMBRELLA},
    )
    state = models.CharField(
        max_length=30,
        choices=WorkRecordState.choices,
        default=WorkRecordState.WORK_SUBMITTED,
        db_index=True,
    )
    period_start = models.DateField(help_text='Start of the work period')
    period_end = models.DateField(help_text='End of the work period')
    hours_worked = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text='Total hours worked in this period',
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Hourly rate at time of submission (snapshot)',
    )
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Calculated gross amount (hours × rate)',
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text='Optimistic locking version — incremented on every state change',
    )
    is_locked = models.BooleanField(
        default=False,
        help_text='Locked after approval — no further edits permitted',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_work_record'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['contractor', 'state']),
            models.Index(fields=['agency', 'state']),
            models.Index(fields=['umbrella', 'state']),
            models.Index(fields=['period_start', 'period_end']),
        ]

    def __str__(self):
        return (
            f"WR-{str(self.id)[:8]} | {self.contractor.email} | "
            f"{self.period_start} to {self.period_end} | {self.get_state_display()}"
        )

    def can_transition_to(self, new_state: str) -> bool:
        """Check if a state transition is valid per the state machine rules."""
        allowed = VALID_STATE_TRANSITIONS.get(self.state, [])
        return new_state in allowed

    def transition_to(self, new_state: str) -> str:
        """
        Attempt a state transition. Returns the previous state.
        Raises ValueError if the transition is invalid.
        """
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition: {self.state} → {new_state}. "
                f"Allowed transitions: {VALID_STATE_TRANSITIONS.get(self.state, [])}"
            )
        previous_state = self.state
        self.state = new_state
        self.version += 1
        return previous_state

    def save(self, *args, **kwargs):
        # Auto-calculate gross amount if not set
        if self.hours_worked and self.hourly_rate and not self.gross_amount:
            self.gross_amount = self.hours_worked * self.hourly_rate
        super().save(*args, **kwargs)
