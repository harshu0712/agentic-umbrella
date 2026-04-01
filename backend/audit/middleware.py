"""
Audit Context Middleware — Module 7

Automatically captures request context (actor, IP, user agent) and
makes it available to the AuditService for every request. This ensures
audit logs always have complete context without requiring each view
to pass this information manually.
"""

import uuid

from audit.services import set_audit_context, clear_audit_context


class AuditContextMiddleware:
    """
    Middleware that sets up audit context for every authenticated request.

    Extracts:
    - Actor (authenticated user)
    - Actor role
    - IP address
    - User agent
    - Request ID (generated or from X-Request-ID header)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or use existing request ID
        request_id = request.headers.get(
            'X-Request-ID',
            str(uuid.uuid4())[:16]
        )

        # Extract actor info from authenticated user
        actor = None
        actor_role = ''
        if hasattr(request, 'user') and request.user.is_authenticated:
            actor = request.user
            actor_role = getattr(request.user, 'role', '')

        # Get client IP (handle proxies)
        ip_address = self._get_client_ip(request)

        # Set thread-local context
        set_audit_context(
            actor=actor,
            actor_role=actor_role,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_id=request_id,
        )

        # Store request_id on the request for downstream use
        request.audit_request_id = request_id

        response = self.get_response(request)

        # Add request ID to response headers for tracing
        response['X-Request-ID'] = request_id

        # Clean up thread-local context
        clear_audit_context()

        return response

    @staticmethod
    def _get_client_ip(request):
        """Extract the real client IP, accounting for proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
