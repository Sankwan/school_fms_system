"""
===========================================
Reports App — Services (Financial Statement Generators)
===========================================
Core report generation logic for:
- Balance Sheet
- Income Statement
- Cash Flow Report
- Budget vs Actual Comparison
"""

from decimal import Decimal
from django.db.models import Sum, F, Q
from django.utils import timezone

from apps.general_ledger.models import ChartOfAccount, JournalEntry, JournalEntryLine
from apps.accounts_receivable.models import Invoice, Payment
from apps.accounts_payable.models import Expense
from .models import Budget, AcademicPeriod


def generate_balance_sheet(as_of_date=None):
    """
    Generate a Balance Sheet as of a specific date.

    The Balance Sheet equation: Assets = Liabilities + Equity

    Returns:
        dict with asset, liability, equity sections and totals
    """
    if as_of_date is None:
        as_of_date = timezone.now().date()

    def _get_accounts_with_balances(account_type):
        """Get accounts of a specific type with their balances."""
        accounts = ChartOfAccount.objects.filter(
            account_type=account_type, is_active=True
        ).order_by('code')

        result = []
        total = Decimal('0.00')
        for account in accounts:
            # Calculate balance from posted journal lines up to date
            lines = JournalEntryLine.objects.filter(
                account=account,
                journal_entry__status=JournalEntry.POSTED,
                journal_entry__date__lte=as_of_date,
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit'),
            )
            debit = lines['total_debit'] or Decimal('0.00')
            credit = lines['total_credit'] or Decimal('0.00')

            if account.balance_type == ChartOfAccount.DEBIT:
                balance = debit - credit
            else:
                balance = credit - debit

            if balance != 0:
                result.append({
                    'code': account.code,
                    'name': account.name,
                    'balance': float(balance),
                })
                total += balance

        return result, float(total)

    assets, total_assets = _get_accounts_with_balances(ChartOfAccount.ASSET)
    liabilities, total_liabilities = _get_accounts_with_balances(ChartOfAccount.LIABILITY)
    equity, total_equity = _get_accounts_with_balances(ChartOfAccount.EQUITY)

    return {
        'title': 'Balance Sheet',
        'as_of_date': str(as_of_date),
        'assets': {'accounts': assets, 'total': total_assets},
        'liabilities': {'accounts': liabilities, 'total': total_liabilities},
        'equity': {'accounts': equity, 'total': total_equity},
        'total_liabilities_and_equity': total_liabilities + total_equity,
        'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < 0.01,
    }


def generate_income_statement(start_date=None, end_date=None):
    """
    Generate an Income Statement (Profit & Loss) for a period.

    Net Income = Total Revenue - Total Expenses

    Args:
        start_date: Start of the reporting period
        end_date: End of the reporting period (defaults to today)
    """
    if end_date is None:
        end_date = timezone.now().date()
    if start_date is None:
        # Default to start of current year
        start_date = end_date.replace(month=1, day=1)

    def _get_period_totals(account_type):
        """Get totals for accounts of a type within the period."""
        accounts = ChartOfAccount.objects.filter(
            account_type=account_type, is_active=True
        ).order_by('code')

        result = []
        total = Decimal('0.00')
        for account in accounts:
            lines = JournalEntryLine.objects.filter(
                account=account,
                journal_entry__status=JournalEntry.POSTED,
                journal_entry__date__gte=start_date,
                journal_entry__date__lte=end_date,
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit'),
            )
            debit = lines['total_debit'] or Decimal('0.00')
            credit = lines['total_credit'] or Decimal('0.00')

            if account.balance_type == ChartOfAccount.CREDIT:
                amount = credit - debit  # Revenue is normally credit
            else:
                amount = debit - credit  # Expense is normally debit

            if amount != 0:
                result.append({
                    'code': account.code,
                    'name': account.name,
                    'amount': float(amount),
                })
                total += amount

        return result, float(total)

    income, total_income = _get_period_totals(ChartOfAccount.INCOME)
    expenses, total_expenses = _get_period_totals(ChartOfAccount.EXPENSE)
    net_income = total_income - total_expenses

    return {
        'title': 'Income Statement',
        'start_date': str(start_date),
        'end_date': str(end_date),
        'income': {'accounts': income, 'total': total_income},
        'expenses': {'accounts': expenses, 'total': total_expenses},
        'net_income': net_income,
    }


def generate_cash_flow(start_date=None, end_date=None):
    """
    Generate a Cash Flow Statement for a period.

    Tracks cash inflows (student payments, other income)
    and cash outflows (expenses, vendor payments).
    """
    if end_date is None:
        end_date = timezone.now().date()
    if start_date is None:
        start_date = end_date.replace(month=1, day=1)

    # Cash inflows from student payments
    payments_received = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Cash outflows from expenses
    expenses_paid = Expense.objects.filter(
        status__in=['approved', 'paid'],
        expense_date__gte=start_date,
        expense_date__lte=end_date,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Detailed breakdown by payment method (inflows)
    payment_breakdown = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
    ).values('payment_method').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Detailed breakdown by category (outflows)
    expense_breakdown = Expense.objects.filter(
        status__in=['approved', 'paid'],
        expense_date__gte=start_date,
        expense_date__lte=end_date,
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    net_cash_flow = float(payments_received) - float(expenses_paid)

    return {
        'title': 'Cash Flow Statement',
        'start_date': str(start_date),
        'end_date': str(end_date),
        'inflows': {
            'total': float(payments_received),
            'breakdown': [
                {'method': item['payment_method'], 'amount': float(item['total'])}
                for item in payment_breakdown
            ],
        },
        'outflows': {
            'total': float(expenses_paid),
            'breakdown': [
                {'category': item['category__name'], 'amount': float(item['total'])}
                for item in expense_breakdown
            ],
        },
        'net_cash_flow': net_cash_flow,
    }


def generate_budget_vs_actual(academic_period_id=None):
    """
    Generate a Budget vs Actual comparison report.

    Compares budgeted amounts against actual expenses
    per category for a specific academic period.
    """
    if academic_period_id:
        period = AcademicPeriod.objects.get(id=academic_period_id)
    else:
        period = AcademicPeriod.objects.filter(is_current=True).first()
        if not period:
            return {'error': 'No current academic period set.'}

    budgets = Budget.objects.filter(
        academic_period=period
    ).select_related('category')

    comparison = []
    total_budgeted = Decimal('0.00')
    total_actual = Decimal('0.00')

    for budget in budgets:
        actual = budget.actual_spent
        comparison.append({
            'category': budget.category.name,
            'category_code': budget.category.code,
            'budgeted': float(budget.amount),
            'actual': float(actual),
            'variance': float(budget.variance),
            'utilization': round(budget.utilization_percentage, 1),
            'status': 'Under Budget' if budget.variance >= 0 else 'Over Budget',
        })
        total_budgeted += budget.amount
        total_actual += actual

    total_variance = total_budgeted - total_actual

    return {
        'title': 'Budget vs Actual',
        'academic_period': str(period),
        'start_date': str(period.start_date),
        'end_date': str(period.end_date),
        'items': comparison,
        'summary': {
            'total_budgeted': float(total_budgeted),
            'total_actual': float(total_actual),
            'total_variance': float(total_variance),
            'overall_utilization': round(
                float(total_actual / total_budgeted * 100) if total_budgeted else 0, 1
            ),
        }
    }
