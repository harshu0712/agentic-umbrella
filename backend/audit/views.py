"""
Audit Log Views — READ-ONLY API endpoints.

The audit log API is strictly read-only. No POST, PUT, PATCH, or DELETE
endpoints are exposed. Audit entries are created programmatically via
AuditService.log() from within other modules.
"""

from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer, AuditLogListSerializer
from audit.filters import AuditLogFilter
from core.pagination import AuditLogPagination
from core.permissions import IsAdminOrPayrollOperator


class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Read-only audit log endpoint.

    Provides:
    - GET /api/v1/audit/logs/ — List all audit entries (paginated, filterable)
    - GET /api/v1/audit/logs/{id}/ — Retrieve a specific audit entry
    - GET /api/v1/audit/logs/event_types/ — List all valid event types
    - GET /api/v1/audit/logs/work_record/{id}/ — All logs for a work record

    No create, update, or delete operations are available.
    """
    queryset = AuditLog.objects.select_related(
        'actor', 'organisation', 'work_record'
    ).all()
    permission_classes = [IsAdminOrPayrollOperator]
    pagination_class = AuditLogPagination
    filterset_class = AuditLogFilter
    search_fields = ['event_type', 'actor__email', 'metadata']
    ordering_fields = ['timestamp', 'event_type']
    ordering = ['-timestamp']

    def get_serializer_class(self):
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer

    @action(detail=False, methods=['get'], url_path='event-types')
    def event_types(self, request):
        """Return all valid audit event types for filtering."""
        from core.enums import AuditEventType
        types = [
            {'value': choice[0], 'label': choice[1]}
            for choice in AuditEventType.choices
        ]
        return Response({'event_types': types})

    @action(
        detail=False, methods=['get'],
        url_path='work-record/(?P<work_record_id>[^/.]+)'
    )
    def by_work_record(self, request, work_record_id=None):
        """Retrieve all audit logs for a specific work record."""
        logs = self.get_queryset().filter(work_record_id=work_record_id)
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = AuditLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Return audit log statistics for dashboard."""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        total = self.get_queryset().count()
        last_24h_count = self.get_queryset().filter(
            timestamp__gte=last_24h
        ).count()
        last_7d_count = self.get_queryset().filter(
            timestamp__gte=last_7d
        ).count()

        by_event_type = (
            self.get_queryset()
            .filter(timestamp__gte=last_7d)
            .values('event_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        return Response({
            'total_entries': total,
            'last_24_hours': last_24h_count,
            'last_7_days': last_7d_count,
            'top_events_7d': list(by_event_type),
        })
