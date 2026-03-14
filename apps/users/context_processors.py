"""
Context processor to inject user permissions into all templates.
Used by the sidebar to show/hide menu items based on the user's role.
"""


def user_permissions(request):
    """Add role permission flags to the template context."""
    if not request.user.is_authenticated:
        return {}

    user = request.user
    is_admin = user.is_superuser or (user.role and user.role.name == 'administrator')

    return {
        'perms_ledger': is_admin or (user.role and user.role.can_manage_ledger),
        'perms_receivables': is_admin or (user.role and user.role.can_manage_receivables),
        'perms_payables': is_admin or (user.role and user.role.can_manage_payables),
        'perms_approve': is_admin or (user.role and user.role.can_approve_expenses),
        'perms_reports': is_admin or (user.role and user.role.can_view_reports),
        'perms_audit': is_admin or (user.role and user.role.can_view_audit_log),
        'perms_student_ledger': is_admin or (user.role and user.role.can_view_student_ledger),
        'perms_export': is_admin or (user.role and user.role.can_export_reports),
        'perms_budgets': is_admin or (user.role and user.role.can_manage_budgets),
    }
