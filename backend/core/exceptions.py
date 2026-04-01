"""
Custom exception handling for the Agentic Umbrella Platform API.

Provides consistent error response format across all endpoints.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent JSON error responses.

    Response format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": {} or []  (optional)
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': {
                'code': _get_error_code(response.status_code),
                'message': _get_error_message(response),
                'details': response.data,
            }
        }
        response.data = error_data
    else:
        # Unhandled exceptions — log and return 500
        logger.exception(
            'Unhandled exception in %s',
            context.get('view', 'unknown'),
            exc_info=exc,
        )
        response = Response(
            {
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected error occurred. Please try again later.',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_code(status_code):
    """Map HTTP status codes to error codes."""
    code_map = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        409: 'CONFLICT',
        429: 'RATE_LIMITED',
        500: 'INTERNAL_SERVER_ERROR',
    }
    return code_map.get(status_code, 'UNKNOWN_ERROR')


def _get_error_message(response):
    """Extract a human-readable message from the DRF response."""
    if isinstance(response.data, dict):
        if 'detail' in response.data:
            return str(response.data['detail'])
        if 'non_field_errors' in response.data:
            return str(response.data['non_field_errors'][0])
    if isinstance(response.data, list) and response.data:
        return str(response.data[0])
    return 'An error occurred.'


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, current_state, target_state, allowed_transitions=None):
        self.current_state = current_state
        self.target_state = target_state
        self.allowed_transitions = allowed_transitions or []
        super().__init__(
            f"Invalid state transition: {current_state} → {target_state}. "
            f"Allowed: {allowed_transitions}"
        )


class PayrollBlockedError(Exception):
    """Raised when payroll is attempted before payment is confirmed."""
    def __init__(self, work_record_id, current_state):
        self.work_record_id = work_record_id
        self.current_state = current_state
        super().__init__(
            f"Payroll blocked for Work Record {work_record_id}. "
            f"Current state: {current_state}. Required: PAYMENT_RECEIVED."
        )


class ComplianceValidationError(Exception):
    """Raised when pre-payroll compliance validation fails."""
    def __init__(self, check_results):
        self.check_results = check_results
        failed_checks = [c for c in check_results if not c['passed']]
        super().__init__(
            f"Compliance validation failed. {len(failed_checks)} check(s) failed."
        )


class ExceptionBlockingError(Exception):
    """Raised when an unresolved exception blocks workflow progression."""
    def __init__(self, exception_id, work_record_id):
        self.exception_id = exception_id
        self.work_record_id = work_record_id
        super().__init__(
            f"Workflow blocked by unresolved exception {exception_id} "
            f"on Work Record {work_record_id}."
        )
