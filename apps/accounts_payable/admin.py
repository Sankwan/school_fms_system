"""Accounts Payable App — Django Admin."""

from django.contrib import admin
from .models import Vendor, ExpenseCategory, Expense, ExpenseApproval, RecurringSchedule


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active']
    search_fields = ['name', 'contact_person']
    list_filter = ['is_active']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'vendor', 'amount', 'status', 'expense_date', 'submitted_by']
    list_filter = ['status', 'category', 'is_recurring']
    search_fields = ['description', 'vendor__name']


@admin.register(ExpenseApproval)
class ExpenseApprovalAdmin(admin.ModelAdmin):
    list_display = ['expense', 'approved_by', 'status', 'approved_at']
    list_filter = ['status']


@admin.register(RecurringSchedule)
class RecurringScheduleAdmin(admin.ModelAdmin):
    list_display = ['expense', 'interval', 'next_due_date', 'is_active']
    list_filter = ['interval', 'is_active']
