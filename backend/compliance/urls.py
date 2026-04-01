"""Compliance URL configuration — Module 6."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from compliance.views import (
    ComplianceCheckViewSet,
    RTISubmissionViewSet,
    StatutoryDocumentViewSet,
    ComplianceReportViewSet,
)

app_name = 'compliance'

router = DefaultRouter()
router.register(r'checks', ComplianceCheckViewSet, basename='compliance-check')
router.register(r'rti', RTISubmissionViewSet, basename='rti-submission')
router.register(r'documents', StatutoryDocumentViewSet, basename='statutory-document')
router.register(r'reports', ComplianceReportViewSet, basename='compliance-report')

urlpatterns = [
    path('', include(router.urls)),
]
