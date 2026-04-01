"""Compliance filters for API endpoints."""

import django_filters
from compliance.models import ComplianceCheck, RTISubmission, StatutoryDocument


class ComplianceCheckFilter(django_filters.FilterSet):
    passed = django_filters.BooleanFilter(field_name='all_passed')
    checked_after = django_filters.DateTimeFilter(
        field_name='checked_at', lookup_expr='gte'
    )
    checked_before = django_filters.DateTimeFilter(
        field_name='checked_at', lookup_expr='lte'
    )

    class Meta:
        model = ComplianceCheck
        fields = ['work_record', 'contractor', 'organisation', 'all_passed']


class RTISubmissionFilter(django_filters.FilterSet):
    class Meta:
        model = RTISubmission
        fields = ['submission_type', 'status', 'organisation', 'tax_year', 'tax_period']


class StatutoryDocumentFilter(django_filters.FilterSet):
    class Meta:
        model = StatutoryDocument
        fields = ['document_type', 'contractor', 'organisation', 'tax_year']
