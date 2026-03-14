"""General Ledger App — Django Admin Configuration."""

from django.contrib import admin
from .models import ChartOfAccount, JournalEntry, JournalEntryLine


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2
    min_num = 2


@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'balance_type', 'parent', 'is_active']
    list_filter = ['account_type', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['code']


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'date', 'description', 'status', 'created_by', 'total_debit']
    list_filter = ['status', 'date']
    search_fields = ['entry_number', 'description']
    inlines = [JournalEntryLineInline]
    readonly_fields = ['entry_number', 'created_by', 'posted_by', 'posted_at']
