"""Accounts Receivable App — Web Views."""

from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Student, Invoice, Payment
from .services import create_invoice, record_payment, get_student_ledger
from apps.users.models import ActivityLog
from apps.users.decorators import role_required


@role_required('can_manage_receivables')
def students_view(request):
    students = Student.objects.filter(is_active=True)
    return render(request, 'receivable/students.html', {'students': students})


@role_required('can_manage_receivables')
def student_form_view(request, student_id=None):
    """Create or edit a student."""
    student = get_object_or_404(Student, id=student_id) if student_id else None

    if request.method == 'POST':
        data = {
            'student_id': request.POST.get('student_id', '').strip(),
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'program': request.POST.get('program', '').strip(),
            'year_level': request.POST.get('year_level', '1'),
            'enrollment_date': request.POST.get('enrollment_date'),
            'guardian_name': request.POST.get('guardian_name', '').strip(),
            'guardian_phone': request.POST.get('guardian_phone', '').strip(),
            'guardian_email': request.POST.get('guardian_email', '').strip(),
        }

        if not data['student_id'] or not data['first_name'] or not data['last_name']:
            messages.error(request, 'Student ID, first name, and last name are required.')
            return render(request, 'receivable/student_form.html', {'student': student})

        try:
            if student:
                for key, value in data.items():
                    setattr(student, key, value)
                student.full_clean()
                student.save()
                ActivityLog.log(
                    user=request.user, action=ActivityLog.ACTION_UPDATE,
                    model_name='Student', object_id=str(student.id),
                    description=f'Updated student: {student.full_name}',
                )
                messages.success(request, f'Student {student.full_name} updated successfully.')
            else:
                student = Student(**data)
                student.full_clean()
                student.save()
                ActivityLog.log(
                    user=request.user, action=ActivityLog.ACTION_CREATE,
                    model_name='Student', object_id=str(student.id),
                    description=f'Registered student: {student.full_name} ({student.student_id})',
                )
                messages.success(request, f'Student {student.full_name} registered successfully.')
            return redirect('students')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'receivable/student_form.html', {'student': student})


@role_required('can_manage_receivables')
def student_delete_view(request, student_id):
    """Deactivate a student (soft delete)."""
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.is_active = False
        student.save()
        ActivityLog.log(
            user=request.user, action=ActivityLog.ACTION_DELETE,
            model_name='Student', object_id=str(student.id),
            description=f'Deactivated student: {student.full_name}',
        )
        messages.success(request, f'Student {student.full_name} deactivated.')
        return redirect('students')
    return render(request, 'shared/delete_confirm.html', {
        'object_name': f'{student.full_name} ({student.student_id})',
        'message': 'This will deactivate the student. Their financial records will be preserved.',
        'action_label': 'Deactivate',
        'cancel_url': '/receivable/students/',
    })


@role_required('can_manage_receivables')
def invoices_view(request):
    invoices = Invoice.objects.select_related('student').all()[:100]
    return render(request, 'receivable/invoices.html', {'invoices': invoices})


@role_required('can_manage_receivables')
def invoice_form_view(request):
    """Create a new invoice using the service layer."""
    students = Student.objects.filter(is_active=True)

    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            description = request.POST.get('description', '').strip()
            amount = request.POST.get('amount', '0')
            due_date = request.POST.get('due_date')
            academic_year = request.POST.get('academic_year', '').strip()
            term = request.POST.get('term', '').strip()

            if not student_id or not description or not due_date or not academic_year:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'receivable/invoice_form.html', {'students': students})

            invoice = create_invoice(
                user=request.user,
                student_id=int(student_id),
                description=description,
                amount=Decimal(amount),
                due_date=due_date,
                academic_year=academic_year,
                term=term,
            )
            messages.success(request, f'Invoice {invoice.invoice_number} created — GH₵{invoice.amount:,.2f}')
            return redirect('invoices')
        except Exception as e:
            messages.error(request, f'Error creating invoice: {str(e)}')

    return render(request, 'receivable/invoice_form.html', {'students': students})


@role_required('can_manage_receivables')
def payments_view(request):
    payments = Payment.objects.select_related('invoice__student').all()[:100]
    return render(request, 'receivable/payments.html', {'payments': payments})


@role_required('can_manage_receivables')
def payment_form_view(request):
    """Record a payment using the service layer."""
    invoices = Invoice.objects.filter(
        status__in=['unpaid', 'partial', 'overdue']
    ).select_related('student')
    selected_invoice_id = request.GET.get('invoice_id')
    if selected_invoice_id:
        selected_invoice_id = int(selected_invoice_id)

    if request.method == 'POST':
        try:
            invoice_id = request.POST.get('invoice')
            amount = request.POST.get('amount', '0')
            payment_method = request.POST.get('payment_method')
            payment_date = request.POST.get('payment_date')
            reference = request.POST.get('reference', '').strip()
            notes = request.POST.get('notes', '').strip()

            if not invoice_id or not payment_method or not payment_date:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'receivable/payment_form.html', {
                    'invoices': invoices, 'selected_invoice_id': selected_invoice_id,
                })

            payment = record_payment(
                user=request.user,
                invoice_id=int(invoice_id),
                amount=Decimal(amount),
                payment_method=payment_method,
                payment_date=payment_date,
                reference=reference,
                notes=notes,
            )
            messages.success(request, f'Payment of GH₵{payment.amount:,.2f} recorded successfully.')
            return redirect('payments')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'receivable/payment_form.html', {
        'invoices': invoices, 'selected_invoice_id': selected_invoice_id,
    })


@role_required('can_view_student_ledger')
def student_ledger_view(request, student_id):
    ledger = get_student_ledger(student_id=student_id)
    return render(request, 'receivable/student_ledger.html', {'ledger': ledger})
