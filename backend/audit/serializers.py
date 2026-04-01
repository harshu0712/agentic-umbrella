"""Audit log serializers — read-only representations."""

from rest_framework import serializers
from audit.models import AuditLog
from core.serializers import UserMinimalSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    """Full audit log entry representation."""
    actor_detail = UserMinimalSerializer(source='actor', read_only=True)
    organisation_name = serializers.CharField(
        source='organisation.name', read_only=True, default=''
    )
    work_record_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'actor', 'actor_detail', 'actor_role',
            'organisation', 'organisation_name', 'event_type',
            'work_record', 'work_record_display',
            'before_state', 'after_state', 'metadata',
            'ip_address', 'user_agent', 'request_id',
        ]
        read_only_fields = fields

    def get_work_record_display(self, obj):
        if obj.work_record:
            return f"WR-{str(obj.work_record_id)[:8]}"
        return None


class AuditLogListSerializer(serializers.ModelSerializer):
    """Compact audit log representation for list views."""
    actor_email = serializers.CharField(
        source='actor.email', read_only=True, default='SYSTEM'
    )

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'actor_email', 'actor_role',
            'event_type', 'work_record',
            'before_state', 'after_state',
        ]
        read_only_fields = fields
