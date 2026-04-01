"""Compliance serializers — Module 6."""

from rest_framework import serializers
from compliance.models import (
    ComplianceCheck,
    RTISubmission,
    StatutoryDocument,
    ComplianceReport,
)
from core.serializers import UserMinimalSerializer


class ComplianceCheckSerializer(serializers.ModelSerializer):
    """Compliance check results."""
    contractor_email = serializers.CharField(
        source='contractor.email', read_only=True
    )
    work_record_display = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceCheck
        fields = [
            'id', 'work_record', 'work_record_display',
            'contractor', 'contractor_email', 'organisation',
            'checks', 'all_passed', 'failed_checks_count',
            'checked_at',
        ]
        read_only_fields = fields

    def get_work_record_display(self, obj):
        return f"WR-{str(obj.work_record_id)[:8]}"


class RTISubmissionSerializer(serializers.ModelSerializer):
    """RTI submission details."""
    can_retry = serializers.BooleanField(read_only=True)
    submission_type_display = serializers.CharField(
        source='get_submission_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = RTISubmission
        fields = [
            'id', 'submission_type', 'submission_type_display',
            'work_record', 'organisation', 'contractor',
            'payload', 'response_data',
            'status', 'status_display', 'error_message',
            'retry_count', 'max_retries', 'can_retry',
            'tax_year', 'tax_period',
            'created_at', 'submitted_at', 'responded_at',
        ]
        read_only_fields = fields


class RTISubmissionListSerializer(serializers.ModelSerializer):
    """Compact RTI submission for list views."""
    can_retry = serializers.BooleanField(read_only=True)

    class Meta:
        model = RTISubmission
        fields = [
            'id', 'submission_type', 'status', 'tax_year',
            'tax_period', 'retry_count', 'can_retry', 'created_at',
        ]
        read_only_fields = fields


class StatutoryDocumentSerializer(serializers.ModelSerializer):
    """Statutory document details."""
    contractor_email = serializers.CharField(
        source='contractor.email', read_only=True
    )
    document_type_display = serializers.CharField(
        source='get_document_type_display', read_only=True
    )
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = StatutoryDocument
        fields = [
            'id', 'document_type', 'document_type_display',
            'contractor', 'contractor_email',
            'work_record', 'organisation',
            'file_name', 'file_size', 'financial_data',
            'tax_year', 'period_start', 'period_end',
            'generated_at', 'retention_until', 'download_url',
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class ComplianceReportSerializer(serializers.ModelSerializer):
    """Compliance report details."""
    class Meta:
        model = ComplianceReport
        fields = [
            'id', 'report_type', 'title', 'organisation',
            'report_data', 'period_start', 'period_end',
            'generated_at',
        ]
        read_only_fields = fields


class RunComplianceCheckSerializer(serializers.Serializer):
    """Request serializer for running a compliance check."""
    work_record_id = serializers.UUIDField()


class GenerateReportSerializer(serializers.Serializer):
    """Request serializer for generating a report."""
    report_type = serializers.ChoiceField(
        choices=['umbrella_payroll_summary', 'agency_cost_report']
    )
    organisation_id = serializers.UUIDField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()

    def validate(self, data):
        if data['period_start'] > data['period_end']:
            raise serializers.ValidationError(
                'period_start must be before period_end.'
            )
        return data
