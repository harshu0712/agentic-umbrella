"""
RBAC Permission classes for the Agentic Umbrella Platform.

Every API endpoint must declare its minimum required role.
Principle of least privilege — default to no access.
"""

from rest_framework.permissions import BasePermission

from core.enums import UserRole


class IsPlatformAdmin(BasePermission):
    """Only platform administrators."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.PLATFORM_ADMIN
        )


class IsAgencyAdmin(BasePermission):
    """Agency admin or higher."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                UserRole.PLATFORM_ADMIN,
                UserRole.AGENCY_ADMIN,
            ]
        )


class IsUmbrellaAdmin(BasePermission):
    """Umbrella company admin or higher."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                UserRole.PLATFORM_ADMIN,
                UserRole.UMBRELLA_ADMIN,
            ]
        )


class IsPayrollOperator(BasePermission):
    """Payroll operator, umbrella admin, or platform admin."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                UserRole.PLATFORM_ADMIN,
                UserRole.UMBRELLA_ADMIN,
                UserRole.PAYROLL_OPERATOR,
            ]
        )


class IsContractor(BasePermission):
    """Contractor users only."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.CONTRACTOR
        )


class IsAdminOrPayrollOperator(BasePermission):
    """Any admin role or payroll operator."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                UserRole.PLATFORM_ADMIN,
                UserRole.AGENCY_ADMIN,
                UserRole.UMBRELLA_ADMIN,
                UserRole.PAYROLL_OPERATOR,
            ]
        )


class IsAnyAdmin(BasePermission):
    """Any admin-level role (platform, agency, or umbrella)."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                UserRole.PLATFORM_ADMIN,
                UserRole.AGENCY_ADMIN,
                UserRole.UMBRELLA_ADMIN,
            ]
        )


class IsOwnRecordOrAdmin(BasePermission):
    """
    Allow access if:
    - User is accessing their own data, OR
    - User is an admin
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role in [
            UserRole.PLATFORM_ADMIN,
            UserRole.AGENCY_ADMIN,
            UserRole.UMBRELLA_ADMIN,
        ]:
            return True

        # Check if the object belongs to the requesting user
        if hasattr(obj, 'contractor'):
            return obj.contractor == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'recipient'):
            return obj.recipient == request.user
        return False
