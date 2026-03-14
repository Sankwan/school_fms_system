"""
===========================================
Users App — Custom Permissions
===========================================
DRF permission classes for role-based access control.
These are used as decorators or in view permission_classes.

Usage in views:
    permission_classes = [IsAuthenticated, IsAdministrator]
    or
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
"""

from rest_framework.permissions import BasePermission


class IsAdministrator(BasePermission):
    """Only allow access to users with Administrator role."""
    message = 'Administrator access required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_administrator()
        )


class IsAccountant(BasePermission):
    """Only allow access to users with Accountant role."""
    message = 'Accountant access required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_accountant()
        )


class IsFinanceOfficer(BasePermission):
    """Only allow access to users with Finance Officer role."""
    message = 'Finance Officer access required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_finance_officer()
        )


class IsAuditor(BasePermission):
    """Only allow access to users with Auditor role."""
    message = 'Auditor access required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_auditor()
        )


class IsTeacher(BasePermission):
    """Only allow access to users with Teacher role."""
    message = 'Teacher access required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_teacher()
        )


# -----------------------------------------------
# Combined permission classes (OR logic)
# -----------------------------------------------

class IsAccountantOrAbove(BasePermission):
    """
    Allow access to Administrator, Accountant, or Finance Officer.
    Used for most financial operations.
    """
    message = 'Accountant, Finance Officer, or Administrator access required.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            request.user.is_administrator()
            or request.user.is_accountant()
            or request.user.is_finance_officer()
        )


class CanApproveExpenses(BasePermission):
    """Only allow users with expense approval permission."""
    message = 'Expense approval permission required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_permission('can_approve_expenses')
        )


class CanViewReports(BasePermission):
    """Allow users with report viewing permission."""
    message = 'Report viewing permission required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_permission('can_view_reports')
        )


class CanExportReports(BasePermission):
    """Allow users with report export permission."""
    message = 'Report export permission required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_permission('can_export_reports')
        )


class CanViewAuditLog(BasePermission):
    """Allow users with audit log viewing permission."""
    message = 'Audit log viewing permission required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_permission('can_view_audit_log')
        )


class HasPermission(BasePermission):
    """
    Generic permission class that checks a specific permission flag.
    Set the `permission_name` attribute on the view.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasPermission]
            permission_name = 'can_manage_ledger'
    """
    message = 'You do not have permission to perform this action.'

    def has_permission(self, request, view):
        permission_name = getattr(view, 'permission_name', None)
        if not permission_name:
            return False
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_permission(permission_name)
        )
