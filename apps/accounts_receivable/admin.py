"""Accounts Receivable App — Django Admin."""

from django.contrib import admin
from .models import Student, Invoice, Payment, StudentLedger, LateFeeRule


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'last_name', 'first_name', 'program', 'year_level', 'is_active']
    list_filter = ['program', 'year_level', 'is_active']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['received_by', 'created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'amount', 'amount_paid', 'status', 'due_date']
    list_filter = ['status', 'academic_year']
    search_fields = ['invoice_number', 'student__first_name', 'student__last_name']
    inlines = [PaymentInline]
    readonly_fields = ['invoice_number', 'amount_paid', 'late_fee', 'created_by']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_method', 'payment_date', 'received_by']
    list_filter = ['payment_method', 'payment_date']


@admin.register(LateFeeRule)
class LateFeeRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate_type', 'rate_value', 'grace_period_days', 'max_fee', 'is_active']


@admin.register(StudentLedger)
class StudentLedgerAdmin(admin.ModelAdmin):
    list_display = ['student', 'transaction_date', 'transaction_type', 'debit', 'credit', 'balance']
    list_filter = ['transaction_type']
    search_fields = ['student__student_id', 'student__first_name']
    readonly_fields = ['student', 'transaction_type', 'debit', 'credit', 'balance']
