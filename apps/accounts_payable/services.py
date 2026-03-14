"""
===========================================
Accounts Payable App — Services
===========================================
Business logic for expense management, approval workflow,
and recurring expense processing.
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from .models import Expense, ExpenseApproval, RecurringSchedule
from apps.users.models import ActivityLog


def create_expense(user, vendor_id, category_id, description, amount,
                   expense_date, is_recurring=False, interval=None,
                   next_due_date=None, end_date=None):
    """
    Create a new expense and optionally set up recurring schedule.

    Returns:
        Expense instance
    """
    with transaction.atomic():
        expense = Expense.objects.create(
            vendor_id=vendor_id,
            category_id=category_id,
            description=description,
            amount=Decimal(str(amount)),
            expense_date=expense_date,
            is_recurring=is_recurring,
            submitted_by=user,
        )

        # Create recurring schedule if applicable
        if is_recurring and interval:
            RecurringSchedule.objects.create(
                expense=expense,
                interval=interval,
                next_due_date=next_due_date or expense_date,
                end_date=end_date,
            )

        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_CREATE,
            model_name='Expense',
            object_id=str(expense.id),
            description=f'Created expense: {description} — {amount}',
        )

        return expense


def approve_expense(expense_id, user, notes=''):
    """
    Approve a pending expense.

    Args:
        expense_id: ID of the expense to approve
        user: User approving the expense (must have approval permission)
        notes: Approval notes

    Raises:
        ValidationError if expense is not in PENDING status
    """
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(id=expense_id)

        if expense.status != Expense.PENDING:
            raise ValidationError(
                f'Cannot approve: expense is {expense.get_status_display()}, not Pending.'
            )

        expense.status = Expense.APPROVED
        expense.save()

        ExpenseApproval.objects.create(
            expense=expense,
            approved_by=user,
            status='approved',
            notes=notes,
        )

        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_APPROVE,
            model_name='Expense',
            object_id=str(expense.id),
            description=f'Approved expense: {expense.description} — {expense.amount}',
        )

        return expense


def reject_expense(expense_id, user, notes=''):
    """Reject a pending expense."""
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(id=expense_id)

        if expense.status != Expense.PENDING:
            raise ValidationError(
                f'Cannot reject: expense is {expense.get_status_display()}, not Pending.'
            )

        expense.status = Expense.REJECTED
        expense.save()

        ExpenseApproval.objects.create(
            expense=expense,
            approved_by=user,
            status='rejected',
            notes=notes,
        )

        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_REJECT,
            model_name='Expense',
            object_id=str(expense.id),
            description=f'Rejected expense: {expense.description} — Reason: {notes}',
        )

        return expense


def process_recurring_expenses():
    """
    Process all due recurring expenses by generating new expense entries.
    Should be run daily via cron or management command.

    Returns:
        dict with count of expenses generated
    """
    today = timezone.now().date()
    generated = 0

    schedules = RecurringSchedule.objects.filter(
        is_active=True,
        next_due_date__lte=today,
    ).select_related('expense')

    with transaction.atomic():
        for schedule in schedules:
            # Skip if past end date
            if schedule.end_date and today > schedule.end_date:
                schedule.is_active = False
                schedule.save()
                continue

            original = schedule.expense

            # Create a new expense based on the template
            new_expense = Expense.objects.create(
                vendor=original.vendor,
                category=original.category,
                description=f'{original.description} (Recurring — {today})',
                amount=original.amount,
                expense_date=today,
                is_recurring=False,  # The new one is not itself recurring
                submitted_by=original.submitted_by,
            )

            # Calculate next due date
            if schedule.interval == 'monthly':
                schedule.next_due_date += relativedelta(months=1)
            elif schedule.interval == 'quarterly':
                schedule.next_due_date += relativedelta(months=3)
            elif schedule.interval == 'yearly':
                schedule.next_due_date += relativedelta(years=1)

            schedule.last_generated = today
            schedule.save()
            generated += 1

    return {
        'expenses_generated': generated,
        'date': str(today),
    }
