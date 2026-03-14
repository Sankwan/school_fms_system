"""
===========================================
Accounts Receivable App — Services
===========================================
Business logic for student invoicing, payment processing,
and late fee calculation.
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Student, Invoice, Payment, StudentLedger, LateFeeRule
from apps.users.models import ActivityLog


def create_invoice(user, student_id, description, amount, due_date,
                   academic_year, term='', late_fee_rule_id=None):
    """
    Create a student fee invoice and record it in the student ledger.

    Args:
        user: User creating the invoice
        student_id: ID of the Student
        description: Invoice description
        amount: Invoice amount
        due_date: Payment due date
        academic_year: e.g., '2025/2026'
        term: e.g., 'Semester 1'
        late_fee_rule_id: Optional LateFeeRule ID

    Returns:
        Invoice instance
    """
    with transaction.atomic():
        student = Student.objects.get(id=student_id)

        invoice = Invoice(
            student=student,
            description=description,
            amount=Decimal(str(amount)),
            due_date=due_date,
            academic_year=academic_year,
            term=term,
            created_by=user,
        )
        if late_fee_rule_id:
            invoice.late_fee_rule = LateFeeRule.objects.get(id=late_fee_rule_id)
        invoice.save()

        # Record in student ledger
        last_ledger = StudentLedger.objects.filter(
            student=student
        ).order_by('-created_at').first()
        previous_balance = last_ledger.balance if last_ledger else Decimal('0.00')
        new_balance = previous_balance + invoice.amount

        StudentLedger.objects.create(
            student=student,
            transaction_type='invoice',
            description=f'Invoice {invoice.invoice_number}: {description}',
            debit=invoice.amount,
            balance=new_balance,
            reference_type='Invoice',
            reference_id=invoice.id,
            transaction_date=timezone.now().date(),
        )

        # Log the activity
        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_CREATE,
            model_name='Invoice',
            object_id=str(invoice.id),
            description=f'Created invoice {invoice.invoice_number} for {student.full_name}: {amount}',
        )

        return invoice


def record_payment(user, invoice_id, amount, payment_method, payment_date,
                   reference='', notes=''):
    """
    Record a payment against a student invoice.
    Updates invoice status and student ledger.

    Args:
        user: User recording the payment
        invoice_id: ID of the Invoice
        amount: Payment amount
        payment_method: Payment method (cash, bank_transfer, etc.)
        payment_date: Date of payment
        reference: Payment reference number
        notes: Additional notes

    Returns:
        Payment instance

    Raises:
        ValidationError if payment exceeds outstanding balance
    """
    amount = Decimal(str(amount))

    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)

        # Validate payment amount
        if amount > invoice.outstanding_balance:
            raise ValidationError(
                f'Payment of {amount} exceeds outstanding balance of '
                f'{invoice.outstanding_balance}.'
            )

        if invoice.status == Invoice.CANCELLED:
            raise ValidationError('Cannot make payment on a cancelled invoice.')

        # Create the payment
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            payment_date=payment_date,
            received_by=user,
        )

        # Update invoice totals
        invoice.amount_paid += amount
        invoice.update_status()

        # Record in student ledger
        student = invoice.student
        last_ledger = StudentLedger.objects.filter(
            student=student
        ).order_by('-created_at').first()
        previous_balance = last_ledger.balance if last_ledger else Decimal('0.00')
        new_balance = previous_balance - amount

        StudentLedger.objects.create(
            student=student,
            transaction_type='payment',
            description=f'Payment for {invoice.invoice_number} ({payment_method})',
            credit=amount,
            balance=new_balance,
            reference_type='Payment',
            reference_id=payment.id,
            transaction_date=payment_date,
        )

        # Log the activity
        ActivityLog.log(
            user=user,
            action=ActivityLog.ACTION_CREATE,
            model_name='Payment',
            object_id=str(payment.id),
            description=(
                f'Recorded payment of {amount} for invoice {invoice.invoice_number} '
                f'({student.full_name})'
            ),
        )

        return payment


def calculate_late_fees():
    """
    Calculate and apply late fees to all overdue invoices.
    Should be run periodically (e.g., daily via cron or management command).

    Returns:
        dict with count of invoices processed and total fees applied
    """
    today = timezone.now().date()
    processed = 0
    total_fees = Decimal('0.00')

    # Find overdue invoices that haven't been fully paid
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=today,
        status__in=[Invoice.UNPAID, Invoice.PARTIAL],
        late_fee_rule__isnull=False,
    ).select_related('late_fee_rule', 'student')

    with transaction.atomic():
        for invoice in overdue_invoices:
            days_overdue = (today - invoice.due_date).days
            rule = invoice.late_fee_rule

            new_fee = rule.calculate_fee(invoice.amount, days_overdue)

            # Only update if fee has changed
            if new_fee != invoice.late_fee and new_fee > 0:
                fee_increase = new_fee - invoice.late_fee
                invoice.late_fee = new_fee
                invoice.status = Invoice.OVERDUE
                invoice.save()

                # Record late fee in student ledger
                if fee_increase > 0:
                    student = invoice.student
                    last_ledger = StudentLedger.objects.filter(
                        student=student
                    ).order_by('-created_at').first()
                    previous_balance = last_ledger.balance if last_ledger else Decimal('0.00')

                    StudentLedger.objects.create(
                        student=student,
                        transaction_type='late_fee',
                        description=f'Late fee for {invoice.invoice_number} ({days_overdue} days overdue)',
                        debit=fee_increase,
                        balance=previous_balance + fee_increase,
                        reference_type='Invoice',
                        reference_id=invoice.id,
                        transaction_date=today,
                    )

                    total_fees += fee_increase
                    processed += 1

    return {
        'invoices_processed': processed,
        'total_fees_applied': float(total_fees),
        'date': str(today),
    }


def get_student_ledger(student_id):
    """
    Get the complete financial ledger for a student.

    Returns:
        dict with student info, ledger entries, and summary
    """
    student = Student.objects.get(id=student_id)
    entries = StudentLedger.objects.filter(student=student).order_by('transaction_date', 'created_at')

    return {
        'student': {
            'id': student.id,
            'student_id': student.student_id,
            'name': student.full_name,
            'program': student.program,
        },
        'entries': [
            {
                'date': str(entry.transaction_date),
                'type': entry.get_transaction_type_display(),
                'description': entry.description,
                'debit': float(entry.debit),
                'credit': float(entry.credit),
                'balance': float(entry.balance),
            }
            for entry in entries
        ],
        'total_outstanding': float(student.total_outstanding),
    }
