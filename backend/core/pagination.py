"""Standard pagination classes for the platform API."""

from rest_framework.pagination import PageNumberPagination, CursorPagination


class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for most list endpoints."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsPagination(PageNumberPagination):
    """Pagination for endpoints that may return large datasets."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class AuditLogPagination(CursorPagination):
    """
    Cursor-based pagination for audit logs.

    Cursor pagination is more efficient for large, append-only tables
    and provides consistent results even when new records are being
    inserted during pagination.
    """
    page_size = 50
    ordering = '-timestamp'
    cursor_query_param = 'cursor'
