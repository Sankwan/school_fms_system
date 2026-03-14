"""Reports App — Web Views (Dashboard & Reports Pages)."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import (
    generate_balance_sheet, generate_income_statement,
    generate_cash_flow, generate_budget_vs_actual,
)
from .export import export_report_to_pdf, export_report_to_excel
from .models import AcademicPeriod
from apps.users.decorators import role_required


@login_required
def dashboard_view(request):
    """Main dashboard page with KPI cards and charts — accessible to all logged-in users."""
    from apps.accounts_receivable.models import Student, Invoice
    from apps.accounts_payable.models import Expense
    from apps.general_ledger.models import JournalEntry
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()

    context = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'total_invoices': Invoice.objects.count(),
        'outstanding_amount': Invoice.objects.filter(
            status__in=['unpaid', 'partial', 'overdue']
        ).aggregate(
            total=Sum('amount') - Sum('amount_paid')
        )['total'] or 0,
        'pending_expenses': Expense.objects.filter(status='pending').count(),
        'approved_expenses_total': Expense.objects.filter(
            status__in=['approved', 'paid']
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'recent_entries': JournalEntry.objects.filter(
            status='posted'
        ).order_by('-date')[:5],
        'overdue_invoices': Invoice.objects.filter(
            status='overdue'
        ).select_related('student').order_by('due_date')[:5],
    }
    return render(request, 'dashboard/index.html', context)


@role_required('can_view_reports')
def balance_sheet_view(request):
    as_of_date = request.GET.get('as_of_date')
    report = generate_balance_sheet(as_of_date=as_of_date)
    return render(request, 'reports/balance_sheet.html', {'report': report})


@role_required('can_view_reports')
def income_statement_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report = generate_income_statement(start_date=start_date, end_date=end_date)
    return render(request, 'reports/income_statement.html', {'report': report})


@role_required('can_view_reports')
def cash_flow_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report = generate_cash_flow(start_date=start_date, end_date=end_date)
    return render(request, 'reports/cash_flow.html', {'report': report})


@role_required('can_view_reports')
def budget_vs_actual_view(request):
    period_id = request.GET.get('period_id')
    report = generate_budget_vs_actual(academic_period_id=period_id)
    periods = AcademicPeriod.objects.all()
    return render(request, 'reports/budget_vs_actual.html', {
        'report': report,
        'periods': periods,
    })


@role_required('can_view_audit_log')
def audit_log_view(request):
    from apps.users.models import ActivityLog
    logs = ActivityLog.objects.select_related('user').all()[:200]
    return render(request, 'reports/audit_log.html', {'logs': logs})


@role_required('can_export_reports')
def export_view(request, report_type, export_format):
    """Handle PDF and Excel export requests from the web UI."""
    generators = {
        'balance-sheet': generate_balance_sheet,
        'income-statement': generate_income_statement,
        'cash-flow': generate_cash_flow,
        'budget-vs-actual': generate_budget_vs_actual,
    }
    generator = generators.get(report_type)
    if not generator:
        from django.http import Http404
        raise Http404

    report_data = generator()
    report_type_key = report_type.replace('-', '_')

    if export_format == 'pdf':
        return export_report_to_pdf(report_data, report_type_key)
    elif export_format == 'excel':
        return export_report_to_excel(report_data, report_type_key)
