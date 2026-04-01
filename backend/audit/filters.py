"""Audit log filters for querying the audit trail."""

import django_filters
from audit.models import AuditLog
from core.enums import AuditEventType


class AuditLogFilter(django_filters.FilterSet):
    """
    Comprehensive filter set for querying audit logs.

    Supports filtering by:
    - event_type: exact match or multiple values
    - actor: by user ID
    - work_record: by work record ID
    - organisation: by org ID
    - date range: timestamp_after / timestamp_before
    - actor_role: exact match
    - has_work_record: boolean (filter logs with/without work records)
    """
    event_type = django_filters.ChoiceFilter(choices=AuditEventType.choices)
    event_type_in = django_filters.MultipleChoiceFilter(
        field_name='event_type',
        choices=AuditEventType.choices,
    )
    timestamp_after = django_filters.DateTimeFilter(
        field_name='timestamp',
        lookup_expr='gte',
    )
    timestamp_before = django_filters.DateTimeFilter(
        field_name='timestamp',
        lookup_expr='lte',
    )
    actor_role = django_filters.CharFilter(field_name='actor_role')
    has_work_record = django_filters.BooleanFilter(
        field_name='work_record',
        lookup_expr='isnull',
        exclude=True,
    )

    class Meta:
        model = AuditLog
        fields = [
            'event_type', 'actor', 'work_record',
            'organisation', 'actor_role',
        ]
