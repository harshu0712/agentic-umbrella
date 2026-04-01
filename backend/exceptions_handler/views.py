"""
Exception Handling Views — Module 7

Full lifecycle management for platform exceptions:
- List, retrieve, raise, assign, review, escalate, resolve, comment.
"""

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q

from exceptions_handler.models import PlatformException
from exceptions_handler.serializers import (
    PlatformExceptionSerializer,
    PlatformExceptionListSerializer,
    RaiseExceptionSerializer,
    AssignExceptionSerializer,
    ResolveExceptionSerializer,
    EscalateExceptionSerializer,
    AddCommentSerializer,
)
from exceptions_handler.services import ExceptionService
from core.permissions import IsAdminOrPayrollOperator, IsAnyAdmin
from core.models import User, WorkRecord
from core.enums import ExceptionStatus


class PlatformExceptionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Exception management endpoints.

    - GET / — List all exceptions (filterable)
    - GET /{id}/ — Get exception details with comments
    - POST /raise/ — Raise a new exception
    - POST /{id}/assign/ — Assign to an admin
    - POST /{id}/start-review/ — Start reviewing
    - POST /{id}/escalate/ — Escalate to higher authority
    - POST /{id}/resolve/ — Resolve (with mandatory justification for overrides)
    - POST /{id}/comment/ — Add a comment
    - GET /stats/ — Dashboard statistics
    - GET /my-assigned/ — Exceptions assigned to current user
    """
    permission_classes = [IsAdminOrPayrollOperator]

    def get_queryset(self):
        return PlatformException.objects.select_related(
            'raised_by', 'assigned_to', 'work_record', 'organisation'
        ).prefetch_related('comments__author').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return PlatformExceptionListSerializer
        return PlatformExceptionSerializer

    def get_queryset(self):
        queryset = PlatformException.objects.select_related(
            'raised_by', 'assigned_to', 'work_record', 'organisation'
        ).prefetch_related('comments__author')

        # Allow filtering by status, severity, type
        status_filter = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        exc_type = self.request.query_params.get('exception_type')
        work_record_id = self.request.query_params.get('work_record')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if severity:
            queryset = queryset.filter(severity=severity)
        if exc_type:
            queryset = queryset.filter(exception_type=exc_type)
        if work_record_id:
            queryset = queryset.filter(work_record_id=work_record_id)

        return queryset

    @action(detail=False, methods=['post'], url_path='raise')
    def raise_exception(self, request):
        """Raise a new platform exception."""
        serializer = RaiseExceptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        work_record = None
        if data.get('work_record_id'):
            try:
                work_record = WorkRecord.objects.get(id=data['work_record_id'])
            except WorkRecord.DoesNotExist:
                return Response(
                    {'error': 'Work record not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        exc = ExceptionService.raise_exception(
            exception_type=data['exception_type'],
            title=data['title'],
            description=data['description'],
            work_record=work_record,
            severity=data.get('severity', 'MEDIUM'),
            raised_by=request.user,
            context_data=data.get('context_data', {}),
        )

        return Response(
            PlatformExceptionSerializer(exc).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign the exception to an admin."""
        serializer = AssignExceptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assignee = User.objects.get(id=serializer.validated_data['assigned_to_id'])
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            exc = ExceptionService.assign(pk, assignee)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(PlatformExceptionSerializer(exc).data)

    @action(detail=True, methods=['post'], url_path='start-review')
    def start_review(self, request, pk=None):
        """Move exception to IN_REVIEW status."""
        try:
            exc = ExceptionService.start_review(pk)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PlatformExceptionSerializer(exc).data)

    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate the exception."""
        serializer = EscalateExceptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            exc = ExceptionService.escalate(
                pk, serializer.validated_data['reason']
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PlatformExceptionSerializer(exc).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve the exception."""
        serializer = ResolveExceptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            exc = ExceptionService.resolve(
                exception_id=pk,
                resolution_notes=serializer.validated_data['resolution_notes'],
                justification=serializer.validated_data.get('justification', ''),
                is_override=serializer.validated_data.get('is_override', False),
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PlatformExceptionSerializer(exc).data)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Add a comment to the exception."""
        serializer = AddCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = ExceptionService.add_comment(
                exception_id=pk,
                author=request.user,
                message=serializer.validated_data['message'],
            )
        except PlatformException.DoesNotExist:
            return Response(
                {'error': 'Exception not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        from exceptions_handler.serializers import ExceptionCommentSerializer
        return Response(
            ExceptionCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'], url_path='my-assigned')
    def my_assigned(self, request):
        """Get exceptions assigned to the current user."""
        queryset = self.get_queryset().filter(
            assigned_to=request.user,
        ).exclude(status=ExceptionStatus.RESOLVED)

        serializer = PlatformExceptionListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Dashboard statistics for exceptions."""
        qs = self.get_queryset()
        total = qs.count()
        by_status = dict(
            qs.values_list('status').annotate(count=Count('id')).order_by()
        )
        by_severity = dict(
            qs.values_list('severity').annotate(count=Count('id')).order_by()
        )
        unresolved = qs.exclude(status=ExceptionStatus.RESOLVED).count()

        # SLA breached (unresolved > 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        sla_threshold = timezone.now() - timedelta(hours=24)
        sla_breached = qs.filter(
            created_at__lt=sla_threshold,
        ).exclude(status=ExceptionStatus.RESOLVED).count()

        return Response({
            'total': total,
            'unresolved': unresolved,
            'sla_breached': sla_breached,
            'by_status': by_status,
            'by_severity': by_severity,
        })
