"""Notification serializers."""

from rest_framework import serializers
from django.utils import timezone
from notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Full notification representation."""
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'event_type', 'work_record',
            'title', 'message', 'action_url',
            'channel', 'status', 'is_read', 'read_at',
            'created_at', 'sent_at', 'time_ago',
        ]
        read_only_fields = [
            'id', 'recipient', 'event_type', 'work_record',
            'title', 'message', 'channel', 'status',
            'created_at', 'sent_at',
        ]

    def get_time_ago(self, obj):
        """Human-readable relative time."""
        delta = timezone.now() - obj.created_at
        seconds = delta.total_seconds()

        if seconds < 60:
            return 'just now'
        if seconds < 3600:
            minutes = int(seconds // 60)
            return f'{minutes}m ago'
        if seconds < 86400:
            hours = int(seconds // 3600)
            return f'{hours}h ago'
        days = int(seconds // 86400)
        return f'{days}d ago'


class NotificationListSerializer(serializers.ModelSerializer):
    """Compact notification for list views."""
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'event_type',
            'is_read', 'created_at', 'channel',
        ]
        read_only_fields = fields


class MarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='List of notification IDs to mark as read. '
                  'If empty, marks all as read.',
    )


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """User notification preferences."""
    class Meta:
        model = NotificationPreference
        fields = ['id', 'event_type', 'email_enabled', 'in_app_enabled']
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Use update_or_create to handle upserts
        preference, _ = NotificationPreference.objects.update_or_create(
            user=validated_data['user'],
            event_type=validated_data['event_type'],
            defaults={
                'email_enabled': validated_data.get('email_enabled', True),
                'in_app_enabled': validated_data.get('in_app_enabled', True),
            },
        )
        return preference
