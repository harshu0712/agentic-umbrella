"""Core views — health check and utility endpoints."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection


class HealthCheckView(APIView):
    """
    System health check endpoint.

    Returns service status and database connectivity.
    Used by load balancers, monitoring, and deployment checks.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        # Check database connectivity
        db_healthy = True
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            db_healthy = False

        health_status = {
            'status': 'healthy' if db_healthy else 'degraded',
            'service': 'agentic-umbrella-platform',
            'modules': ['compliance', 'audit', 'notifications', 'exceptions_handler'],
            'database': 'connected' if db_healthy else 'disconnected',
        }

        status_code = 200 if db_healthy else 503
        return Response(health_status, status=status_code)
