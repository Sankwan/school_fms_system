"""
===========================================
Users App — Signals
===========================================
Django signal handlers for login/logout audit logging.
Captures successful login and logout events to the ActivityLog.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import ActivityLog


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful login events."""
    ActivityLog.log(
        user=user,
        action=ActivityLog.ACTION_LOGIN,
        model_name='CustomUser',
        object_id=str(user.id),
        description=f'User {user.email} logged in successfully.',
        request=request,
    )

    # Update last login IP on the user model
    if request:
        ip = ActivityLog._get_client_ip(request)
        user.last_login_ip = ip
        user.failed_login_attempts = 0  # Reset on successful login
        user.save(update_fields=['last_login_ip', 'failed_login_attempts'])


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log logout events."""
    if user:
        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_LOGOUT,
            model_name='CustomUser',
            object_id=str(user.id),
            description=f'User {user.email} logged out.',
            request=request,
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """
    Log failed login attempts for security monitoring.
    Also implements account lockout after 5 consecutive failures.
    """
    from .models import CustomUser

    email = credentials.get('email', credentials.get('username', 'unknown'))

    # Log the failed attempt
    ActivityLog.log(
        user=None,
        action=ActivityLog.ACTION_LOGIN,
        model_name='CustomUser',
        description=f'Failed login attempt for: {email}',
        request=request,
    )

    # Increment failed attempts and lock account if threshold reached
    try:
        user = CustomUser.objects.get(email=email)
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
        user.save(update_fields=['failed_login_attempts', 'is_locked'])
    except CustomUser.DoesNotExist:
        pass  # Unknown email — don't reveal whether account exists
