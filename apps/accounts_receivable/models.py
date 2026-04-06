"""
===========================================
Accounts Receivable App — Models
===========================================
Student invoicing, payment tracking, late fee rules,
and individual student financial ledgers.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal
from datetime import date, datetime


class Student(models.Model):
    """
    Student records for the institution.
    Links to invoices, payments, and the individual student ledger.
    """

    student_id = models.CharField(
        max_length=30, unique=True, blank=True,
        help_text='Institutional student ID (e.g., KG-2025-001)'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    CLASS_CATEGORIES = [
        ('kindergarten', 'Kindergarten'),
        ('primary', 'Primary'),
        ('jhs', 'JHS'),
    ]

    class_category = models.CharField(
        max_length=20,
        choices=CLASS_CATEGORIES,
        default='primary',
        help_text='Current school section (e.g., Primary)'
    )
    class_name = models.CharField(
        max_length=50,
        default='',
        blank=True,
        help_text='Specific class (e.g., Class 1A, JHS 3B)'
    )
    year_level = models.PositiveIntegerField(
        default=1,
        help_text='Numerical level (1 for Class 1, 2 for Class 2, etc.)'
    )
    enrollment_date = models.DateField()
    is_active = models.BooleanField(default=True)

    # Guardian/Parent info
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ar_student'
        ordering = ['last_name', 'first_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['last_name', 'first_name']),
        ]

    def save(self, *args, **kwargs):
        if not self.student_id:
            # Map category to prefix
            prefixes = {
                'kindergarten': 'KG',
                'primary': 'PRI',
                'jhs': 'JHS'
            }
            prefix = prefixes.get(self.class_category, 'STU')
            
            # Use enrollment year (handle if date is passed as string)
            enrollment_date = self.enrollment_date
            if isinstance(enrollment_date, str):
                enrollment_date = date.fromisoformat(enrollment_date)
            
            year = enrollment_date.year if enrollment_date else date.today().year
            
            # Find last student via lexicographical sort of student_id
            pattern = f"{prefix}-{year}-"
            last = Student.objects.filter(student_id__startswith=pattern).order_by('-student_id').first()
            
            if last and last.student_id:
                try:
                    # Extract sequence from end of ID (e.g. "PRI-2026-005" -> 5)
                    seq = int(last.student_id.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.student_id = f"{prefix}-{year}-{seq:03d}"
            
            # Final safety check: ensure the ID is globally unique
            # (handles race conditions or legacy gaps)
            while Student.objects.filter(student_id=self.student_id).exists():
                seq += 1
                self.student_id = f"{prefix}-{year}-{seq:03d}"
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_id} — {self.last_name}, {self.first_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_outstanding(self):
        """Total amount owed by this student across all invoices."""
        from django.db.models import Sum, F
        result = self.invoices.filter(
            status__in=['unpaid', 'partial', 'overdue']
        ).aggregate(
            total=Sum(F('amount') - F('amount_paid'))
        )
        return result['total'] or Decimal('0.00')



class LateFeeRule(models.Model):
    """
    Configurable late fee calculation rules.
    Applied automatically to overdue invoices.
    """

    name = models.CharField(max_length=100, help_text='Rule name (e.g., Standard Late Fee)')
    grace_period_days = models.PositiveIntegerField(
        default=7,
        help_text='Number of days after due date before late fee applies'
    )
    rate_type = models.CharField(
        max_length=20,
        choices=[
            ('percentage', 'Percentage of Invoice Amount'),
            ('fixed', 'Fixed Amount'),
        ],
        default='percentage'
    )
    rate_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Percentage rate (e.g., 2.5%) or fixed amount'
    )
    max_fee = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text='Maximum late fee cap (optional)'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'ar_latefeerule'
        verbose_name = 'Late Fee Rule'
        verbose_name_plural = 'Late Fee Rules'

    def __str__(self):
        return self.name

    def calculate_fee(self, invoice_amount, days_overdue):
        """
        Calculate the late fee for an overdue invoice.

        Args:
            invoice_amount: Total invoice amount
            days_overdue: Number of days past due date

        Returns:
            Decimal fee amount (or 0 if within grace period)
        """
        if days_overdue <= self.grace_period_days:
            return Decimal('0.00')

        if self.rate_type == 'percentage':
            fee = invoice_amount * (self.rate_value / Decimal('100'))
        else:
            fee = self.rate_value

        # Apply maximum cap if set
        if self.max_fee and fee > self.max_fee:
            fee = self.max_fee

        return fee.quantize(Decimal('0.01'))


class Invoice(models.Model):
    """
    Student fee invoice.
    Tracks the amount owed, payments made, and outstanding balance.
    """

    UNPAID = 'unpaid'
    PARTIAL = 'partial'
    PAID = 'paid'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (UNPAID, 'Unpaid'),
        (PARTIAL, 'Partially Paid'),
        (PAID, 'Paid'),
        (OVERDUE, 'Overdue'),
        (CANCELLED, 'Cancelled'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name='invoices'
    )
    invoice_number = models.CharField(
        max_length=30, unique=True, editable=False
    )
    description = models.CharField(
        max_length=300,
        help_text='e.g., Tuition Fee - Semester 1, 2025'
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00')
    )
    late_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=UNPAID)
    due_date = models.DateField()

    # Academic context
    academic_year = models.CharField(max_length=20, help_text='e.g., 2025/2026')
    term = models.CharField(
        max_length=20, blank=True,
        help_text='e.g., Semester 1, Term 2'
    )

    late_fee_rule = models.ForeignKey(
        LateFeeRule, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='invoices_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ar_invoice'
        ordering = ['-created_at']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.invoice_number} — {self.student.full_name} — {self.status}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from django.utils import timezone
            today_str = timezone.now().strftime('%Y%m%d')
            # Look for the last invoice created today
            last = Invoice.objects.filter(invoice_number__startswith=f'INV-{today_str}').order_by('-id').first()
            if last and last.invoice_number:
                try:
                    # Extract the sequence number from the end
                    parts = last.invoice_number.split('-')
                    seq = int(parts[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.invoice_number = f"INV-{today_str}-{seq:04d}"
        super().save(*args, **kwargs)

    @property
    def outstanding_balance(self):
        """Amount still owed including late fees."""
        return (self.amount + self.late_fee) - self.amount_paid

    @property
    def is_overdue(self):
        """Check if the invoice is past its due date."""
        from django.utils import timezone
        return (
            self.due_date < timezone.now().date()
            and self.status in [self.UNPAID, self.PARTIAL]
        )

    def update_status(self):
        """Recalculate the invoice status based on payments."""
        total_due = self.amount + self.late_fee
        if self.amount_paid >= total_due:
            self.status = self.PAID
        elif self.amount_paid > 0:
            self.status = self.PARTIAL
        elif self.is_overdue:
            self.status = self.OVERDUE
        else:
            self.status = self.UNPAID
        self.save()


class Payment(models.Model):
    """
    Individual payment made against a student invoice.
    Records payment method, reference, and creates student ledger entries.
    """

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('card', 'Card Payment'),
        ('other', 'Other'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES
    )
    reference = models.CharField(
        max_length=100, blank=True,
        help_text='Payment reference / receipt number'
    )
    notes = models.TextField(blank=True)
    payment_date = models.DateField()

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='payments_received'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ar_payment'
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice.invoice_number}"


class StudentLedger(models.Model):
    """
    Running financial ledger for each student.
    Records all invoices, payments, and fee adjustments
    as line items with a running balance.
    """

    TRANSACTION_CHOICES = [
        ('invoice', 'Invoice (Charge)'),
        ('payment', 'Payment'),
        ('late_fee', 'Late Fee'),
        ('adjustment', 'Adjustment'),
        ('refund', 'Refund'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='ledger_entries'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES)
    description = models.CharField(max_length=300)
    debit = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Amount charged (increases balance owed)'
    )
    credit = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Amount paid/credited (decreases balance owed)'
    )
    balance = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Running balance after this transaction'
    )

    # Reference to related objects
    reference_type = models.CharField(max_length=50, blank=True)  # 'Invoice', 'Payment'
    reference_id = models.PositiveIntegerField(null=True, blank=True)

    transaction_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ar_studentledger'
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Student Ledger Entry'
        verbose_name_plural = 'Student Ledger Entries'
        indexes = [
            models.Index(fields=['student', 'transaction_date']),
        ]

    def __str__(self):
        return f"{self.student.student_id} — {self.transaction_type} — {self.description}"
class FeeStructure(models.Model):
    """Predefined fee amounts per class category for automatic billing."""
    name = models.CharField(max_length=100, default='Standard Fee')
    category = models.CharField(
        max_length=20,
        choices=Student.CLASS_CATEGORIES,
    )
    term = models.CharField(max_length=20, default='Term 1')
    amount_per_term = models.DecimalField(max_digits=12, decimal_places=2)
    academic_year = models.CharField(max_length=20, help_text='e.g., 2025/2026')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ar_feestructure'
        ordering = ['-academic_year', 'term', 'category']
        verbose_name = 'Fee Structure'
        verbose_name_plural = 'Fee Structures'

    def __str__(self):
        return f"{self.name} ({self.get_category_display()} — {self.term}): GH₵{self.amount_per_term:,.2f}"


class TeacherSalary(models.Model):
    """Monthly salary payment status for teachers."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('delayed', 'Delayed'),
    ]

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='salaries',
        limit_choices_to={'role__name': 'teacher'}
    )
    month = models.PositiveIntegerField()  # 1-12
    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'ar_teachersalary'
        ordering = ['-year', '-month']
        unique_together = ['teacher', 'month', 'year']
        verbose_name = 'Teacher Salary'
        verbose_name_plural = 'Teacher Salaries'

    def __str__(self):
        return f"{self.teacher.get_full_name()} — {self.month}/{self.year} — {self.status}"
