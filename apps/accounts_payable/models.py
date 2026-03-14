"""
===========================================
Accounts Payable App — Models
===========================================
Vendor management, expense tracking, approval workflow,
and recurring expense scheduling.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal


class Vendor(models.Model):
    """
    Vendor/Supplier records.
    Tracks entities from whom the institution procures goods and services.
    """

    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text='Tax Identification Number')
    bank_details = models.TextField(blank=True, help_text='Bank name, account number, etc.')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ap_vendor'
        ordering = ['name']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    @property
    def total_expenses(self):
        """Total approved expenses for this vendor."""
        from django.db.models import Sum
        result = self.expenses.filter(status='approved').aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.00')


class ExpenseCategory(models.Model):
    """Categories for classifying expenses (e.g., Utilities, Salaries, Supplies)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True, help_text='Category code (e.g., EXP-SAL)')

    class Meta:
        db_table = 'ap_expensecategory'
        ordering = ['name']
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return f"{self.code} — {self.name}"


class Expense(models.Model):
    """
    Individual expense/expenditure record.
    Follows an approval workflow: PENDING → APPROVED/REJECTED.
    """

    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    PAID = 'paid'

    STATUS_CHOICES = [
        (PENDING, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (PAID, 'Paid'),
    ]

    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name='expenses',
        null=True, blank=True
    )
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT, related_name='expenses'
    )
    description = models.TextField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    expense_date = models.DateField()
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    payment_reference = models.CharField(max_length=100, blank=True)

    # Recurring expense fields
    is_recurring = models.BooleanField(default=False)

    # Tracking
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='expenses_submitted'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ap_expense'
        ordering = ['-expense_date']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['expense_date']),
            models.Index(fields=['vendor']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.category.name} — {self.amount} ({self.status})"


class ExpenseApproval(models.Model):
    """
    Approval record for expenses.
    Tracks who approved/rejected and when.
    """

    expense = models.OneToOneField(
        Expense, on_delete=models.CASCADE, related_name='approval'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='approvals_given'
    )
    status = models.CharField(
        max_length=20,
        choices=[('approved', 'Approved'), ('rejected', 'Rejected')]
    )
    notes = models.TextField(blank=True, help_text='Approval/rejection reason')
    approved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ap_expenseapproval'
        verbose_name = 'Expense Approval'
        verbose_name_plural = 'Expense Approvals'

    def __str__(self):
        return f"{self.expense} — {self.status} by {self.approved_by}"


class RecurringSchedule(models.Model):
    """
    Schedule for recurring expenses (salaries, utilities, etc.).
    Automatically generates new expense entries on the schedule.
    """

    INTERVAL_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    expense = models.OneToOneField(
        Expense, on_delete=models.CASCADE, related_name='recurring_schedule'
    )
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES)
    next_due_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text='End date for recurrence (leave blank for indefinite)')
    is_active = models.BooleanField(default=True)
    last_generated = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'ap_recurringschedule'
        verbose_name = 'Recurring Schedule'
        verbose_name_plural = 'Recurring Schedules'

    def __str__(self):
        return f"{self.expense.description} — {self.interval}"
