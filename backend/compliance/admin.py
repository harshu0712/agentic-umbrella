from django.contrib import admin
from compliance.models import (
    ComplianceCheck,
    RTISubmission,
    StatutoryDocument,
    ComplianceReport,
)


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['work_record', 'contractor', 'all_passed', 'failed_checks_count', 'checked_at']
    list_filter = ['all_passed', 'checked_at']
    readonly_fields = ['id', 'checked_at']


@admin.register(RTISubmission)
class RTISubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'submission_type', 'organisation', 'status',
        'tax_year', 'tax_period', 'retry_count', 'created_at',
    ]
    list_filter = ['submission_type', 'status', 'tax_year']
    readonly_fields = ['id', 'created_at', 'submitted_at', 'responded_at']


@admin.register(StatutoryDocument)
class StatutoryDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'document_type', 'contractor', 'tax_year',
        'file_name', 'generated_at', 'retention_until',
    ]
    list_filter = ['document_type', 'tax_year']
    search_fields = ['contractor__email', 'file_name']
    readonly_fields = ['id', 'generated_at']


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'organisation', 'period_start', 'period_end', 'generated_at']
    list_filter = ['report_type']
    readonly_fields = ['id', 'generated_at']
