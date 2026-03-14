"""
===========================================
General Ledger App — Web Views (Template-based)
===========================================
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal

from .models import ChartOfAccount, JournalEntry, JournalEntryLine
from .services import create_journal_entry, post_journal_entry, generate_trial_balance
from apps.users.decorators import role_required


@role_required('can_manage_ledger')
def chart_of_accounts_view(request):
    """Display the Chart of Accounts listing."""
    accounts = ChartOfAccount.objects.filter(
        parent__isnull=True, is_active=True
    ).prefetch_related('children')
    return render(request, 'ledger/chart_of_accounts.html', {'accounts': accounts})


@role_required('can_manage_ledger')
def journal_entries_view(request):
    """List all journal entries."""
    entries = JournalEntry.objects.select_related(
        'created_by', 'posted_by'
    ).prefetch_related('lines__account').all()[:100]
    return render(request, 'ledger/journal_entries.html', {'entries': entries})


@role_required('can_manage_ledger', 'can_post_entries')
def journal_entry_form_view(request):
    """Create a new journal entry."""
    accounts = ChartOfAccount.objects.filter(is_active=True).order_by('code')

    if request.method == 'POST':
        date = request.POST.get('date')
        description = request.POST.get('description')
        reference = request.POST.get('reference', '')

        # Parse dynamic line items from the form
        lines_data = []
        line_count = int(request.POST.get('line_count', 0))
        for i in range(line_count):
            account_id = request.POST.get(f'lines-{i}-account')
            debit = request.POST.get(f'lines-{i}-debit', '0') or '0'
            credit = request.POST.get(f'lines-{i}-credit', '0') or '0'
            line_desc = request.POST.get(f'lines-{i}-description', '')

            if account_id:
                lines_data.append({
                    'account_id': int(account_id),
                    'debit': Decimal(debit),
                    'credit': Decimal(credit),
                    'description': line_desc,
                })

        try:
            entry = create_journal_entry(
                user=request.user,
                date=date,
                description=description,
                lines_data=lines_data,
                reference=reference,
            )
            messages.success(request, f'Journal entry {entry.entry_number} created successfully.')
            return redirect('journal-entries')
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'ledger/journal_entry_form.html', {'accounts': accounts})


@role_required('can_manage_ledger')
def trial_balance_view(request):
    """Display the auto-generated trial balance."""
    as_of_date = request.GET.get('as_of_date')
    trial_balance = generate_trial_balance(
        as_of_date=as_of_date if as_of_date else None
    )
    return render(request, 'ledger/trial_balance.html', {'trial_balance': trial_balance})
