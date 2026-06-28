"""Users App — Django Admin Configuration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, ActivityLog


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'can_manage_users', 'can_manage_ledger', 'can_approve_expenses', 'can_view_reports']
    list_filter = ['name']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'is_locked', 'date_joined']
    list_filter = ['role', 'is_active', 'is_locked']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    # Override fieldsets to include custom fields
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {
            'fields': ('role', 'phone', 'department'),
        }),
        ('Security', {
            'fields': ('last_login_ip', 'failed_login_attempts', 'is_locked'),
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['description', 'user__email']
    readonly_fields = [
        'user', 'action', 'model_name', 'object_id', 'description',
        'changes', 'ip_address', 'user_agent', 'request_path', 'timestamp',
    ]
    date_hierarchy = 'timestamp'

    # Audit trail is immutable — view-only in the admin.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
