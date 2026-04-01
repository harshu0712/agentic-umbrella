"""
Compliance Engine Views — Module 6

REST API endpoints for:
- Compliance validation checks
- RTI submission management
- Statutory document access
- Compliance reporting
"""

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from compliance.models import (
    ComplianceCheck,
    RTISubmission,
    StatutoryDocument,
    ComplianceReport,
)
from compliance.serializers import (
    ComplianceCheckSerializer,
    RTISubmissionSerializer,
    RTISubmissionListSerializer,
    StatutoryDocumentSerializer,
    ComplianceReportSerializer,
    RunComplianceCheckSerializer,
    GenerateReportSerializer,
)
from compliance.services import (
    ComplianceValidationService,
    RTIGeneratorService,
    ComplianceReportingService,
)
from core.permissions import (
    IsAdminOrPayrollOperator,
    IsPayrollOperator,
    IsOwnRecordOrAdmin,
    IsContractor,
)
from core.models import WorkRecord, Organisation


class ComplianceCheckViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Compliance check endpoints.

    - GET /compliance/checks/ — List all compliance checks
    - GET /compliance/checks/{id}/ — Get check details
    - POST /compliance/checks/run/ — Run a compliance check on a work record
    """
    serializer_class = ComplianceCheckSerializer
    permission_classes = [IsAdminOrPayrollOperator]

    def get_queryset(self):
        queryset = ComplianceCheck.objects.select_related(
            'contractor', 'work_record', 'organisation'
        ).all()

        work_record_id = self.request.query_params.get('work_record')
        if work_record_id:
            queryset = queryset.filter(work_record_id=work_record_id)

        passed = self.request.query_params.get('passed')
        if passed is not None:
            queryset = queryset.filter(all_passed=passed.lower() == 'true')

        return queryset

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a compliance validation check on a work record."""
        serializer = RunComplianceCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            work_record = WorkRecord.objects.get(
                id=serializer.validated_data['work_record_id']
            )
        except WorkRecord.DoesNotExist:
            return Response(
                {'error': 'Work record not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        check = ComplianceValidationService.validate(work_record)
        return Response(
            ComplianceCheckSerializer(check).data,
            status=status.HTTP_201_CREATED,
        )


class RTISubmissionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    RTI submission endpoints.

    - GET /compliance/rti/ — List all RTI submissions
    - GET /compliance/rti/{id}/ — Get submission details
    - POST /compliance/rti/{id}/submit/ — Submit to HMRC
    - POST /compliance/rti/{id}/retry/ — Retry a failed submission
    - GET /compliance/rti/stats/ — Submission statistics
    """
    permission_classes = [IsPayrollOperator]

    def get_queryset(self):
        queryset = RTISubmission.objects.select_related(
            'organisation', 'work_record', 'contractor'
        ).all()

        submission_type = self.request.query_params.get('type')
        if submission_type:
            queryset = queryset.filter(submission_type=submission_type)

        rti_status = self.request.query_params.get('status')
        if rti_status:
            queryset = queryset.filter(status=rti_status)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return RTISubmissionListSerializer
        return RTISubmissionSerializer

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit an RTI record to HMRC."""
        try:
            submission = RTIGeneratorService.submit(pk)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(RTISubmissionSerializer(submission).data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed RTI submission."""
        try:
            submission = RTISubmission.objects.get(id=pk)
        except RTISubmission.DoesNotExist:
            return Response(
                {'error': 'Submission not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not submission.can_retry:
            return Response(
                {'error': 'Submission cannot be retried. Max retries exceeded or wrong status.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission = RTIGeneratorService.submit(pk)
        return Response(RTISubmissionSerializer(submission).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """RTI submission statistics."""
        from django.db.models import Count
        qs = self.get_queryset()

        by_status = dict(
            qs.values_list('status').annotate(count=Count('id')).order_by()
        )
        by_type = dict(
            qs.values_list('submission_type').annotate(count=Count('id')).order_by()
        )

        return Response({
            'total': qs.count(),
            'by_status': by_status,
            'by_type': by_type,
        })


class StatutoryDocumentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Statutory document endpoints (Payslips, P45, P60).

    - GET /compliance/documents/ — List documents
    - GET /compliance/documents/{id}/ — Get document details
    - GET /compliance/documents/{id}/download/ — Download PDF

    Contractors can only see their own documents.
    Admins can see all documents in their organisation.
    """
    serializer_class = StatutoryDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = StatutoryDocument.objects.select_related(
            'contractor', 'organisation', 'work_record'
        )

        # Contractors only see their own documents
        if user.role == 'CONTRACTOR':
            queryset = queryset.filter(contractor=user)
        # Admins see org-scoped documents
        elif user.role in ['UMBRELLA_ADMIN', 'PAYROLL_OPERATOR']:
            org_ids = user.memberships.values_list('organisation_id', flat=True)
            queryset = queryset.filter(organisation_id__in=org_ids)

        # Filters
        doc_type = self.request.query_params.get('type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)

        tax_year = self.request.query_params.get('tax_year')
        if tax_year:
            queryset = queryset.filter(tax_year=tax_year)

        return queryset

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the document PDF."""
        from django.http import FileResponse
        document = self.get_object()

        if not document.file:
            return Response(
                {'error': 'File not available.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            document.file.open('rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=document.file_name,
        )


class ComplianceReportViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Compliance report endpoints.

    - GET /compliance/reports/ — List reports
    - GET /compliance/reports/{id}/ — Get report details
    - POST /compliance/reports/generate/ — Generate a new report
    """
    serializer_class = ComplianceReportSerializer
    permission_classes = [IsAdminOrPayrollOperator]

    def get_queryset(self):
        return ComplianceReport.objects.select_related('organisation').all()

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a compliance report."""
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            organisation = Organisation.objects.get(id=data['organisation_id'])
        except Organisation.DoesNotExist:
            return Response(
                {'error': 'Organisation not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if data['report_type'] == 'umbrella_payroll_summary':
            report_data = ComplianceReportingService.generate_umbrella_payroll_summary(
                organisation, data['period_start'], data['period_end']
            )
        elif data['report_type'] == 'agency_cost_report':
            report_data = ComplianceReportingService.generate_agency_cost_report(
                organisation, data['period_start'], data['period_end']
            )
        else:
            return Response(
                {'error': f"Unknown report type: {data['report_type']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(report_data, status=status.HTTP_201_CREATED)
