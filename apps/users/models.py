"""
===========================================
Users App — Models
===========================================
Custom user model with role-based access control,
and activity logging for audit trail.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Role(models.Model):
    """
    System roles for RBAC.
    Each role defines a set of permission flags that control
    what areas of the system a user can access.
    """

    # Role name constants
    ADMINISTRATOR = 'administrator'
    ACCOUNTANT = 'accountant'
    FINANCE_OFFICER = 'finance_officer'
    AUDITOR = 'auditor'
    TEACHER = 'teacher'

    ROLE_CHOICES = [
        (ADMINISTRATOR, 'Administrator'),
        (ACCOUNTANT, 'Accountant'),
        (FINANCE_OFFICER, 'Finance Officer'),
        (AUDITOR, 'Auditor'),
        (TEACHER, 'Teacher'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    # Granular permission flags
    can_manage_users = models.BooleanField(default=False)
    can_manage_ledger = models.BooleanField(default=False)      # Chart of Accounts, Journal Entries
    can_post_entries = models.BooleanField(default=False)        # Finalize/post journal entries
    can_manage_receivables = models.BooleanField(default=False)  # Invoices, payments
    can_manage_payables = models.BooleanField(default=False)     # Vendors, expenses
    can_approve_expenses = models.BooleanField(default=False)    # Expense approval workflow
    can_view_reports = models.BooleanField(default=False)        # Financial reports
    can_export_reports = models.BooleanField(default=False)      # PDF/Excel export
    can_manage_budgets = models.BooleanField(default=False)      # Budget allocation
    can_view_audit_log = models.BooleanField(default=False)      # Audit trail access
    can_view_student_ledger = models.BooleanField(default=False) # Student financial ledger

    class Meta:
        db_table = 'users_role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.get_name_display()


class CustomUser(AbstractUser):
    """
    Extended user model with role assignment, profile fields,
    and security tracking. Uses email as the primary identifier.
    """

    email = models.EmailField(unique=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,  # Prevent deletion of roles with assigned users
        related_name='users',
        null=True,
        blank=True
    )

    # Profile fields
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)

    # Security tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    # Use email for authentication instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users_customuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    # -----------------------------------------------
    # Role helper methods
    # -----------------------------------------------
    def is_administrator(self):
        """Check if user has Administrator role."""
        return self.role and self.role.name == Role.ADMINISTRATOR

    def is_accountant(self):
        """Check if user has Accountant role."""
        return self.role and self.role.name == Role.ACCOUNTANT

    def is_finance_officer(self):
        """Check if user has Finance Officer role."""
        return self.role and self.role.name == Role.FINANCE_OFFICER

    def is_auditor(self):
        """Check if user has Auditor role."""
        return self.role and self.role.name == Role.AUDITOR

    def is_teacher(self):
        """Check if user has Teacher role."""
        return self.role and self.role.name == Role.TEACHER

    def has_permission(self, permission_name):
        """
        Check if the user's role grants a specific permission.
        Example: user.has_permission('can_manage_ledger')
        """
        if not self.role:
            return False
        return getattr(self.role, permission_name, False)


class ActivityLog(models.Model):
    """
    Comprehensive audit trail for all system activities.
    Tracks user actions, financial transactions, and security events
    for regulatory compliance and accountability.
    """

    # Action type constants
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_APPROVE = 'approve'
    ACTION_REJECT = 'reject'
    ACTION_POST = 'post'        # Post a journal entry
    ACTION_EXPORT = 'export'    # Export a report
    ACTION_VIEW = 'view'

    ACTION_CHOICES = [
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_APPROVE, 'Approve'),
        (ACTION_REJECT, 'Reject'),
        (ACTION_POST, 'Post'),
        (ACTION_EXPORT, 'Export'),
        (ACTION_VIEW, 'View'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)  # e.g., 'JournalEntry'
    object_id = models.CharField(max_length=50, blank=True)    # ID of affected object
    description = models.TextField(blank=True)                  # Human-readable description
    changes = models.JSONField(null=True, blank=True)           # Before/after values for updates

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'users_activitylog'
        ordering = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'System'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_str} — {self.action} {self.model_name}"

    @classmethod
    def log(cls, user, action, model_name='', object_id='',
            description='', changes=None, request=None):
        """
        Convenience method to create an activity log entry.

        Usage:
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.ACTION_CREATE,
                model_name='JournalEntry',
                object_id=str(entry.id),
                description='Created journal entry JE-0001',
                request=request,
            )
        """
        log_entry = cls(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            description=description,
            changes=changes,
        )
        if request:
            log_entry.ip_address = cls._get_client_ip(request)
            log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
            log_entry.request_path = request.path
            log_entry.request_method = request.method

        log_entry.save()
        return log_entry

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request, considering proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
