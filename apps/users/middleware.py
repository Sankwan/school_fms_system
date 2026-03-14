"""
===========================================
Users App — Middleware
===========================================
Custom middleware for audit trail logging.
Automatically logs all write operations (POST, PUT, PATCH, DELETE)
to the ActivityLog for complete audit coverage.
"""

import json
import logging
from .models import ActivityLog

logger = logging.getLogger(__name__)


class AuditTrailMiddleware:
    """
    Middleware that automatically logs all state-changing HTTP requests.

    - POST, PUT, PATCH, DELETE requests are logged
    - GET requests are NOT logged to avoid noise
    - API and admin paths are included
    - Static/media file requests are excluded
    """

    # Paths to exclude from audit logging
    EXCLUDED_PREFIXES = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/__debug__/',  # Django Debug Toolbar
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)

        # Only log state-changing methods
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            self._log_request(request, response)

        return response

    def _log_request(self, request, response):
        """Create an audit log entry for the request."""
        # Skip excluded paths
        if any(request.path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return

        # Skip if user is not authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return

        # Skip if response indicates auth failure
        if response.status_code in (401, 403):
            return

        try:
            # Determine the action type from the HTTP method
            method_action_map = {
                'POST': ActivityLog.ACTION_CREATE,
                'PUT': ActivityLog.ACTION_UPDATE,
                'PATCH': ActivityLog.ACTION_UPDATE,
                'DELETE': ActivityLog.ACTION_DELETE,
            }
            action = method_action_map.get(request.method, 'unknown')

            # Build description
            description = f"{request.method} {request.path} — Status: {response.status_code}"

            ActivityLog.log(
                user=request.user,
                action=action,
                description=description,
                request=request,
            )
        except Exception as e:
            # Never let audit logging crash the request
            logger.error(f"AuditTrailMiddleware error: {e}")
