"""
===========================================
Reports App — Models
===========================================
Budget planning and academic period models
for the reporting engine.
"""

from django.db import models
from decimal import Decimal


class AcademicPeriod(models.Model):
    """Academic year/term for contexting financial data."""

    year = models.CharField(max_length=20, help_text='e.g., 2025/2026')
    term = models.CharField(max_length=50, blank=True, help_text='e.g., Semester 1')
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = 'reports_academicperiod'
        ordering = ['-start_date']
        verbose_name = 'Academic Period'
        verbose_name_plural = 'Academic Periods'
        unique_together = ['year', 'term']

    def __str__(self):
        return f"{self.year} — {self.term}" if self.term else self.year


class Budget(models.Model):
    """
    Budget allocations per expense category per academic period.
    Used for Budget vs Actual comparison reports.
    """

    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    category = models.ForeignKey(
        'accounts_payable.ExpenseCategory',
        on_delete=models.PROTECT,
        related_name='budgets'
    )
    academic_period = models.ForeignKey(
        AcademicPeriod, on_delete=models.PROTECT,
        related_name='budgets'
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Budgeted amount for this category in this period'
    )
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='yearly')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reports_budget'
        ordering = ['category', 'academic_period']
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'
        unique_together = ['category', 'academic_period']

    def __str__(self):
        return f"{self.category.name} — {self.academic_period} — {self.amount}"

    @property
    def actual_spent(self):
        """Calculate actual expenses in this category for this period."""
        from apps.accounts_payable.models import Expense
        from django.db.models import Sum

        result = Expense.objects.filter(
            category=self.category,
            status__in=['approved', 'paid'],
            expense_date__gte=self.academic_period.start_date,
            expense_date__lte=self.academic_period.end_date,
        ).aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.00')

    @property
    def variance(self):
        """Budget variance: positive means under budget, negative means over budget."""
        return self.amount - self.actual_spent

    @property
    def utilization_percentage(self):
        """Percentage of budget utilized."""
        if self.amount > 0:
            return float((self.actual_spent / self.amount) * 100)
        return 0.0
