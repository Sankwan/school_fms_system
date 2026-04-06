"""
===========================================
General Ledger App — Models
===========================================
Implements a proper double-entry bookkeeping system with:
- Chart of Accounts (hierarchical, 5 account types)
- Journal Entries with multiple lines
- Double-entry balance enforcement at model level
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal


class ChartOfAccount(models.Model):
    """
    Chart of Accounts — the foundation of the general ledger.

    Every financial transaction flows through these accounts.
    Accounts are organized hierarchically (parent/child) and categorized
    into 5 standard types per GAAP/IFRS:
      - Assets (Debit normal)
      - Liabilities (Credit normal)
      - Equity (Credit normal)
      - Income/Revenue (Credit normal)
      - Expenses (Debit normal)
    """

    # Account type definitions
    ASSET = 'asset'
    LIABILITY = 'liability'
    EQUITY = 'equity'
    INCOME = 'income'
    EXPENSE = 'expense'

    ACCOUNT_TYPE_CHOICES = [
        (ASSET, 'Asset'),
        (LIABILITY, 'Liability'),
        (EQUITY, 'Equity'),
        (INCOME, 'Income / Revenue'),
        (EXPENSE, 'Expense'),
    ]

    # Balance type: determines whether the account normally carries
    # a debit balance or a credit balance
    DEBIT = 'debit'
    CREDIT = 'credit'
    BALANCE_TYPE_CHOICES = [
        (DEBIT, 'Debit'),
        (CREDIT, 'Credit'),
    ]

    # Account identifier (e.g., "1000", "1100", "2000")
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique account code (e.g., 1000 for Cash)'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    balance_type = models.CharField(
        max_length=10,
        choices=BALANCE_TYPE_CHOICES,
        help_text='Normal balance side for this account'
    )

    # Hierarchical structure (sub-accounts)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text='Parent account for sub-account grouping'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gl_chartofaccount'
        ordering = ['code']
        verbose_name = 'Chart of Account'
        verbose_name_plural = 'Chart of Accounts'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['account_type']),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        """Auto-set balance_type based on account_type if not specified."""
        if not self.balance_type:
            # Assets and Expenses are normally debit; all others are credit
            if self.account_type in (self.ASSET, self.EXPENSE):
                self.balance_type = self.DEBIT
            else:
                self.balance_type = self.CREDIT
        super().save(*args, **kwargs)

    @property
    def balance(self):
        """
        Calculate the current balance of this account from all posted journal lines.
        For debit-normal accounts: balance = sum(debits) - sum(credits)
        For credit-normal accounts: balance = sum(credits) - sum(debits)
        """
        from django.db.models import Sum

        lines = self.journal_lines.filter(
            journal_entry__status=JournalEntry.POSTED
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
        )

        total_debit = lines['total_debit'] or Decimal('0.00')
        total_credit = lines['total_credit'] or Decimal('0.00')

        if self.balance_type == self.DEBIT:
            return total_debit - total_credit
        else:
            return total_credit - total_debit


class JournalEntry(models.Model):
    """
    Journal Entry header — represents a single financial transaction.

    Each journal entry must have at least 2 lines (one debit, one credit)
    and the total debits MUST equal total credits (double-entry principle).

    Lifecycle: DRAFT → POSTED (irreversible once posted)
    Posted entries cannot be edited — only reversed via new entries.
    """

    DRAFT = 'draft'
    POSTED = 'posted'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (POSTED, 'Posted'),
    ]

    # Auto-generated entry number (e.g., JE-0001)
    entry_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Auto-generated entry number'
    )
    date = models.DateField(help_text='Transaction date')
    description = models.TextField(help_text='Narrative describing the transaction')
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text='External reference (invoice #, receipt #, etc.)'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)

    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='journal_entries_created'
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries_posted'
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gl_journalentry'
        ordering = ['-date', '-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'
        indexes = [
            models.Index(fields=['entry_number']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.entry_number} — {self.description[:50]}"

    def save(self, *args, **kwargs):
        """Auto-generate entry number and reference if not set."""
        if not self.entry_number:
            last_entry = JournalEntry.objects.order_by('-id').first()
            next_num = (last_entry.id + 1) if last_entry else 1
            self.entry_number = f"JE-{next_num:05d}"
            
        if not self.reference:
            from django.utils import timezone
            now = timezone.now()
            # Simple systematic reference: REF-YYYYMMDD-ID
            # To ensure it's unique even before save (if we want to show it), 
            # we'd need a different approach, but for now this works.
            # We'll use the ID of the last entry + 1
            last_entry = JournalEntry.objects.order_by('-id').first()
            next_id = (last_entry.id + 1) if last_entry else 1
            self.reference = f"REF-{now.strftime('%Y%m%d')}-{next_id:04d}"
            
        super().save(*args, **kwargs)

    def clean(self):
        """
        DOUBLE-ENTRY ENFORCEMENT (Level 1: Model validation)
        Ensures total debits equal total credits before save.
        """
        if self.pk:  # Only validate existing entries with lines
            self.validate_balance()

    def validate_balance(self):
        """
        Core double-entry validation.
        Raises ValidationError if debits ≠ credits.
        """
        totals = self.lines.aggregate(
            total_debit=models.Sum('debit'),
            total_credit=models.Sum('credit'),
        )
        total_debit = totals['total_debit'] or Decimal('0.00')
        total_credit = totals['total_credit'] or Decimal('0.00')

        if total_debit != total_credit:
            raise ValidationError(
                f'Journal entry is not balanced. '
                f'Total Debits: {total_debit}, Total Credits: {total_credit}. '
                f'Difference: {abs(total_debit - total_credit)}'
            )

    @property
    def total_debit(self):
        """Sum of all debit amounts in this entry."""
        return self.lines.aggregate(
            total=models.Sum('debit')
        )['total'] or Decimal('0.00')

    @property
    def total_credit(self):
        """Sum of all credit amounts in this entry."""
        return self.lines.aggregate(
            total=models.Sum('credit')
        )['total'] or Decimal('0.00')

    @property
    def is_balanced(self):
        """Check if the entry is balanced (debits == credits)."""
        return self.total_debit == self.total_credit

    @property
    def line_count(self):
        """Number of lines in this journal entry."""
        return self.lines.count()


class JournalEntryLine(models.Model):
    """
    Individual line within a journal entry.
    Each line debits OR credits a specific account.

    Rules:
    - A line can have a debit amount OR a credit amount, not both.
    - At least one of debit/credit must be > 0.
    - The parent JournalEntry must have ≥ 2 lines.
    """

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name='journal_lines'
    )
    description = models.CharField(max_length=300, blank=True)
    debit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Debit amount (enter 0 if this is a credit line)'
    )
    credit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Credit amount (enter 0 if this is a debit line)'
    )

    class Meta:
        db_table = 'gl_journalentryline'
        verbose_name = 'Journal Entry Line'
        verbose_name_plural = 'Journal Entry Lines'

    def __str__(self):
        side = 'DR' if self.debit > 0 else 'CR'
        amount = self.debit if self.debit > 0 else self.credit
        return f"{self.account.code} — {side} {amount}"

    def clean(self):
        """
        Validate that each line has either a debit OR a credit, not both,
        and that the amount is positive.
        """
        if self.debit > 0 and self.credit > 0:
            raise ValidationError(
                'A journal line cannot have both a debit and credit amount. '
                'Use one or the other.'
            )
        if self.debit == 0 and self.credit == 0:
            raise ValidationError(
                'A journal line must have either a debit or credit amount greater than zero.'
            )
        if self.debit < 0 or self.credit < 0:
            raise ValidationError(
                'Debit and credit amounts cannot be negative.'
            )
