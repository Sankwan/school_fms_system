"""
===========================================
General Ledger App — Services (Business Logic)
===========================================
Core accounting operations isolated from views.
This is where double-entry bookkeeping rules are enforced.
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, Q

from .models import ChartOfAccount, JournalEntry, JournalEntryLine
from apps.users.models import ActivityLog


def create_journal_entry(user, date, description, lines_data, reference=''):
    """
    Create a complete journal entry with all its lines in a single
    atomic transaction. Enforces double-entry at every level.

    Args:
        user: The user creating the entry
        date: Transaction date
        description: Narrative for the transaction
        lines_data: List of dicts, each with:
            - account_id: int (ChartOfAccount ID)
            - debit: Decimal (or 0)
            - credit: Decimal (or 0)
            - description: str (optional line description)
        reference: External reference string (optional)

    Returns:
        JournalEntry instance

    Raises:
        ValidationError if:
        - Less than 2 lines provided
        - Total debits ≠ total credits
        - A line has both debit and credit
        - An account doesn't exist or is inactive

    Example:
        entry = create_journal_entry(
            user=request.user,
            date='2025-01-15',
            description='Record tuition fee income from student payments',
            lines_data=[
                {'account_id': 1, 'debit': Decimal('5000.00'), 'credit': Decimal('0.00'),
                 'description': 'Cash received'},
                {'account_id': 10, 'debit': Decimal('0.00'), 'credit': Decimal('5000.00'),
                 'description': 'Tuition fee income'},
            ],
            reference='INV-2025-001',
        )
    """

    # -----------------------------------------------
    # Validation Level 1: Pre-save checks
    # -----------------------------------------------
    if len(lines_data) < 2:
        raise ValidationError(
            'A journal entry must have at least 2 lines '
            '(minimum one debit and one credit).'
        )

    # Calculate totals before saving anything
    total_debit = sum(Decimal(str(line.get('debit', 0))) for line in lines_data)
    total_credit = sum(Decimal(str(line.get('credit', 0))) for line in lines_data)

    if total_debit != total_credit:
        raise ValidationError(
            f'Entry is not balanced. '
            f'Total Debits: {total_debit}, Total Credits: {total_credit}. '
            f'Difference: {abs(total_debit - total_credit)}'
        )

    if total_debit == Decimal('0.00'):
        raise ValidationError('Total debit/credit amount cannot be zero.')

    # -----------------------------------------------
    # Validation Level 2: Atomic database transaction
    # -----------------------------------------------
    with transaction.atomic():
        # Create the header
        entry = JournalEntry(
            date=date,
            description=description,
            reference=reference,
            status=JournalEntry.DRAFT,
            created_by=user,
        )
        entry.save()

        # Create each line
        for line_data in lines_data:
            account = ChartOfAccount.objects.get(id=line_data['account_id'])

            if not account.is_active:
                raise ValidationError(
                    f'Account {account.code} — {account.name} is inactive.'
                )

            line = JournalEntryLine(
                journal_entry=entry,
                account=account,
                debit=Decimal(str(line_data.get('debit', 0))),
                credit=Decimal(str(line_data.get('credit', 0))),
                description=line_data.get('description', ''),
            )
            line.full_clean()  # Validate each line individually
            line.save()

        # -----------------------------------------------
        # Validation Level 3: Post-save balance check
        # -----------------------------------------------
        entry.validate_balance()

        # Log the creation
        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_CREATE,
            model_name='JournalEntry',
            object_id=str(entry.id),
            description=f'Created journal entry {entry.entry_number}: {description}',
        )

        return entry


def post_journal_entry(entry_id, user):
    """
    Finalize (post) a draft journal entry.
    Once posted, the entry cannot be modified — only reversed.

    This is a critical operation that moves the entry from DRAFT to POSTED,
    permanently affecting account balances.

    Args:
        entry_id: ID of the JournalEntry to post
        user: The user posting the entry

    Returns:
        The posted JournalEntry

    Raises:
        ValidationError if entry is not balanced or already posted
    """
    with transaction.atomic():
        entry = JournalEntry.objects.select_for_update().get(id=entry_id)

        if entry.status == JournalEntry.POSTED:
            raise ValidationError('This entry has already been posted.')

        # Final balance verification before posting
        entry.validate_balance()

        # Minimum line count check
        if entry.line_count < 2:
            raise ValidationError(
                'Cannot post: entry must have at least 2 lines.'
            )

        # Post the entry
        entry.status = JournalEntry.POSTED
        entry.posted_by = user
        entry.posted_at = timezone.now()
        entry.save()

        # Log the posting
        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_POST,
            model_name='JournalEntry',
            object_id=str(entry.id),
            description=f'Posted journal entry {entry.entry_number}',
        )

        return entry


def generate_trial_balance(as_of_date=None):
    """
    Generate a Trial Balance report.

    The trial balance lists all accounts with their debit or credit balances.
    In a correctly maintained double-entry system, total debits = total credits.

    Args:
        as_of_date: Date to generate trial balance as of (defaults to today)

    Returns:
        dict with:
        - accounts: list of account balances
        - total_debit: sum of all debit balances
        - total_credit: sum of all credit balances
        - is_balanced: bool indicating if TB is balanced
    """
    if as_of_date is None:
        as_of_date = timezone.now().date()

    # Get all active accounts
    accounts = ChartOfAccount.objects.filter(is_active=True).order_by('code')

    trial_balance = []
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')

    for account in accounts:
        # Calculate balance from posted entries up to the given date
        lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__status=JournalEntry.POSTED,
            journal_entry__date__lte=as_of_date,
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
        )

        acc_debit = lines['total_debit'] or Decimal('0.00')
        acc_credit = lines['total_credit'] or Decimal('0.00')

        # Calculate net balance based on normal balance type
        if account.balance_type == ChartOfAccount.DEBIT:
            net = acc_debit - acc_credit
            debit_balance = net if net >= 0 else Decimal('0.00')
            credit_balance = abs(net) if net < 0 else Decimal('0.00')
        else:
            net = acc_credit - acc_debit
            credit_balance = net if net >= 0 else Decimal('0.00')
            debit_balance = abs(net) if net < 0 else Decimal('0.00')

        # Only include accounts with non-zero balance
        if debit_balance != 0 or credit_balance != 0:
            trial_balance.append({
                'account_code': account.code,
                'account_name': account.name,
                'account_type': account.get_account_type_display(),
                'debit': float(debit_balance),
                'credit': float(credit_balance),
            })
            total_debit += debit_balance
            total_credit += credit_balance

    return {
        'as_of_date': str(as_of_date),
        'accounts': trial_balance,
        'total_debit': float(total_debit),
        'total_credit': float(total_credit),
        'is_balanced': total_debit == total_credit,
    }
