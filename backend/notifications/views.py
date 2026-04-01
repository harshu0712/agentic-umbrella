"""
Notification Views — Module 7

Endpoints for managing in-app notifications and preferences.
Users can only see their own notifications.
"""

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from notifications.models import Notification, NotificationPreference
from notifications.serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    MarkReadSerializer,
    NotificationPreferenceSerializer,
)
from core.pagination import StandardResultsPagination


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Notification endpoints for the authenticated user.

    - GET /notifications/ — List all notifications
    - GET /notifications/{id}/ — Get a specific notification
    - POST /notifications/mark-read/ — Mark specific notifications as read
    - POST /notifications/mark-all-read/ — Mark all notifications as read
    - GET /notifications/unread-count/ — Get count of unread notifications
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        """Users can only see their own notifications."""
        return Notification.objects.filter(
            recipient=self.request.user,
            channel='IN_APP',
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_read(self, request):
        """Mark specific notifications as read."""
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids', [])

        queryset = self.get_queryset().filter(is_read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)

        updated = queryset.update(is_read=True, read_at=timezone.now())

        return Response({
            'marked_read': updated,
            'message': f'{updated} notification(s) marked as read.',
        })

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all unread notifications as read."""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({
            'marked_read': updated,
            'message': f'{updated} notification(s) marked as read.',
        })

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get the count of unread notifications."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=True, methods=['post'], url_path='read')
    def mark_single_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return Response(NotificationSerializer(notification).data)


class NotificationPreferenceViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Manage notification preferences.

    - GET /notifications/preferences/ — List current preferences
    - POST /notifications/preferences/ — Create/update a preference
    - PUT /notifications/preferences/{id}/ — Update a preference
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
