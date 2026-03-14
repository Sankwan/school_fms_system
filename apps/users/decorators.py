"""
Role-based permission decorators for web views.
Uses the Role model's granular permission flags.
"""

from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def role_required(*permissions):
    """
    Decorator that checks if the user's role has ALL specified permissions.
    Administrators bypass all checks.

    Usage:
        @role_required('can_manage_receivables')
        def students_view(request):
            ...

        @role_required('can_manage_ledger', 'can_post_entries')
        def post_journal_entry(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Superusers and admins bypass permission checks
            if user.is_superuser or (user.role and user.role.name == 'administrator'):
                return view_func(request, *args, **kwargs)

            # Check if user has all required permissions
            if not user.role:
                return render(request, 'shared/access_denied.html', {
                    'message': 'No role assigned. Contact your administrator.',
                }, status=403)

            for perm in permissions:
                if not getattr(user.role, perm, False):
                    return render(request, 'shared/access_denied.html', {
                        'message': f'You do not have permission to access this page.',
                        'required': perm.replace('can_', '').replace('_', ' ').title(),
                    }, status=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
