"""Exception handling serializers."""

from rest_framework import serializers
from exceptions_handler.models import PlatformException, ExceptionComment
from core.serializers import UserMinimalSerializer


class ExceptionCommentSerializer(serializers.ModelSerializer):
    """Comment on an exception."""
    author_detail = UserMinimalSerializer(source='author', read_only=True)

    class Meta:
        model = ExceptionComment
        fields = ['id', 'author', 'author_detail', 'message', 'created_at']
        read_only_fields = ['id', 'author', 'author_detail', 'created_at']


class PlatformExceptionSerializer(serializers.ModelSerializer):
    """Full exception representation."""
    comments = ExceptionCommentSerializer(many=True, read_only=True)
    raised_by_detail = UserMinimalSerializer(source='raised_by', read_only=True)
    assigned_to_detail = UserMinimalSerializer(source='assigned_to', read_only=True)
    sla_hours_elapsed = serializers.FloatField(read_only=True)
    is_blocking = serializers.BooleanField(read_only=True)

    class Meta:
        model = PlatformException
        fields = [
            'id', 'exception_type', 'severity', 'title', 'description',
            'work_record', 'organisation', 'status',
            'raised_by', 'raised_by_detail',
            'assigned_to', 'assigned_to_detail',
            'resolution_notes', 'justification', 'is_override',
            'context_data', 'is_blocking', 'sla_hours_elapsed',
            'created_at', 'updated_at', 'assigned_at', 'resolved_at',
            'comments',
        ]
        read_only_fields = [
            'id', 'status', 'raised_by', 'resolved_at',
            'assigned_at', 'created_at', 'updated_at',
        ]


class PlatformExceptionListSerializer(serializers.ModelSerializer):
    """Compact exception for list views."""
    assigned_to_email = serializers.CharField(
        source='assigned_to.email', read_only=True, default=None
    )
    sla_hours_elapsed = serializers.FloatField(read_only=True)

    class Meta:
        model = PlatformException
        fields = [
            'id', 'exception_type', 'severity', 'title', 'status',
            'assigned_to_email', 'work_record',
            'sla_hours_elapsed', 'created_at',
        ]
        read_only_fields = fields


class RaiseExceptionSerializer(serializers.Serializer):
    """Serializer for raising a new exception."""
    exception_type = serializers.ChoiceField(choices=PlatformException._meta.get_field('exception_type').choices)
    severity = serializers.ChoiceField(choices=PlatformException._meta.get_field('severity').choices, default='MEDIUM')
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    work_record_id = serializers.UUIDField(required=False, allow_null=True)
    context_data = serializers.JSONField(required=False, default=dict)


class AssignExceptionSerializer(serializers.Serializer):
    """Serializer for assigning an exception."""
    assigned_to_id = serializers.UUIDField()


class ResolveExceptionSerializer(serializers.Serializer):
    """Serializer for resolving an exception."""
    resolution_notes = serializers.CharField()
    justification = serializers.CharField(required=False, default='')
    is_override = serializers.BooleanField(default=False)

    def validate(self, data):
        if data.get('is_override') and not data.get('justification', '').strip():
            raise serializers.ValidationError(
                'Manual overrides require a mandatory written justification. '
                'This is a compliance requirement.'
            )
        return data


class EscalateExceptionSerializer(serializers.Serializer):
    """Serializer for escalating an exception."""
    reason = serializers.CharField()


class AddCommentSerializer(serializers.Serializer):
    """Serializer for adding a comment to an exception."""
    message = serializers.CharField()
