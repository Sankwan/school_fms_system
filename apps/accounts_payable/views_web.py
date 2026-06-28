"""Accounts Payable App — Web Views."""

from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from apps.users.models import ActivityLog
from apps.users.decorators import role_required
from .models import Vendor, Expense, ExpenseCategory, ExpenseApproval


@role_required('can_manage_payables')
def vendors_view(request):
    vendors = Vendor.objects.filter(is_active=True)
    return render(request, 'payable/vendors.html', {'vendors': vendors})


@role_required('can_manage_payables')
def vendor_form_view(request, vendor_id=None):
    """Create or edit a vendor."""
    vendor = get_object_or_404(Vendor, id=vendor_id) if vendor_id else None

    if request.method == 'POST':
        data = {
            'name': request.POST.get('name', '').strip(),
            'contact_person': request.POST.get('contact_person', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'tax_id': request.POST.get('tax_id', '').strip(),
            'bank_details': request.POST.get('bank_details', '').strip(),
            'notes': request.POST.get('notes', '').strip(),
        }

        if not data['name']:
            messages.error(request, 'Vendor name is required.')
            return render(request, 'payable/vendor_form.html', {'vendor': vendor})

        try:
            if vendor:
                changes = ActivityLog.diff(vendor, data)
                for key, value in data.items():
                    setattr(vendor, key, value)
                vendor.full_clean()
                vendor.save()
                ActivityLog.log(
                    user=request.user, action=ActivityLog.ACTION_UPDATE,
                    model_name='Vendor', object_id=str(vendor.id),
                    description=f'Updated vendor: {vendor.name}',
                    changes=changes,
                )
                messages.success(request, f'Vendor {vendor.name} updated successfully.')
            else:
                vendor = Vendor(**data)
                vendor.full_clean()
                vendor.save()
                ActivityLog.log(
                    user=request.user, action=ActivityLog.ACTION_CREATE,
                    model_name='Vendor', object_id=str(vendor.id),
                    description=f'Added vendor: {vendor.name}',
                )
                messages.success(request, f'Vendor {vendor.name} added successfully.')
            return redirect('vendors')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'payable/vendor_form.html', {'vendor': vendor})


@role_required('can_manage_payables')
def vendor_delete_view(request, vendor_id):
    """Deactivate a vendor (soft delete)."""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        vendor.is_active = False
        vendor.save()
        ActivityLog.log(
            user=request.user, action=ActivityLog.ACTION_DELETE,
            model_name='Vendor', object_id=str(vendor.id),
            description=f'Deactivated vendor: {vendor.name}',
        )
        messages.success(request, f'Vendor {vendor.name} deactivated.')
        return redirect('vendors')
    return render(request, 'shared/delete_confirm.html', {
        'object_name': vendor.name,
        'message': 'This will deactivate the vendor. Existing expense records will be preserved.',
        'action_label': 'Deactivate',
        'cancel_url': '/payable/vendors/',
    })


@role_required('can_manage_payables')
def expenses_view(request):
    expenses = Expense.objects.select_related('vendor', 'category', 'submitted_by').all()[:100]
    return render(request, 'payable/expenses.html', {'expenses': expenses})


@role_required('can_manage_payables')
def expense_form_view(request):
    vendors = Vendor.objects.filter(is_active=True)
    categories = ExpenseCategory.objects.all()

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            vendor_id = request.POST.get('vendor')
            description = request.POST.get('description', '').strip()
            amount_str = request.POST.get('amount', '0')
            expense_date = request.POST.get('expense_date')

            if not category_id or not description or not expense_date:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'payable/expense_form.html', {
                    'vendors': vendors, 'categories': categories,
                })

            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    raise ValueError
            except (InvalidOperation, ValueError):
                messages.error(request, 'Please enter a valid positive amount.')
                return render(request, 'payable/expense_form.html', {
                    'vendors': vendors, 'categories': categories,
                })

            category = ExpenseCategory.objects.get(id=category_id)
            vendor = Vendor.objects.get(id=vendor_id) if vendor_id else None

            expense = Expense(
                category=category, vendor=vendor,
                description=description, amount=amount,
                expense_date=expense_date,
                status=Expense.PENDING,
                submitted_by=request.user,
            )

            if 'receipt' in request.FILES:
                expense.receipt = request.FILES['receipt']

            expense.full_clean()
            expense.save()

            ActivityLog.log(
                user=request.user, action=ActivityLog.ACTION_CREATE,
                model_name='Expense', object_id=str(expense.id),
                description=f'Submitted expense: {description} — GH₵{amount:,.2f}',
            )
            messages.success(request, f'Expense submitted for approval — GH₵{amount:,.2f}')
            return redirect('expenses')

        except ExpenseCategory.DoesNotExist:
            messages.error(request, 'Invalid expense category.')
        except Vendor.DoesNotExist:
            messages.error(request, 'Invalid vendor selected.')
        except Exception as e:
            messages.error(request, f'Error submitting expense: {str(e)}')

    return render(request, 'payable/expense_form.html', {
        'vendors': vendors, 'categories': categories,
    })


@role_required('can_approve_expenses')
def approvals_view(request):
    pending = Expense.objects.filter(status='pending').select_related('vendor', 'category', 'submitted_by')
    return render(request, 'payable/approvals.html', {'expenses': pending})


@role_required('can_approve_expenses')
def expense_approve_view(request, expense_id):
    """Approve a pending expense safely."""
    expense = get_object_or_404(Expense, id=expense_id, status=Expense.PENDING)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                notes = request.POST.get('notes', '').strip()
                
                # Update status
                expense.status = Expense.APPROVED
                expense.save(update_fields=['status', 'updated_at'])
                
                # Use update_or_create to prevent IntegrityError on re-submission/race condition
                ExpenseApproval.objects.update_or_create(
                    expense=expense,
                    defaults={
                        'approved_by': request.user,
                        'status': 'approved',
                        'notes': notes,
                    }
                )
                
                ActivityLog.log(
                    user=request.user, action=ActivityLog.ACTION_UPDATE,
                    model_name='Expense', object_id=str(expense.id),
                    description=f'Approved expense: {expense.description} — GH₵{expense.amount:,.2f}',
                )
                
            messages.success(request, f'Expense approved — GH₵{expense.amount:,.2f}')
        except Exception as e:
            # Provide more detailed error info
            messages.error(request, f'Approval failed: {str(e)}')
            
    return redirect('approvals')


@role_required('can_approve_expenses')
def expense_reject_view(request, expense_id):
    """Reject a pending expense safely."""
    expense = get_object_or_404(Expense, id=expense_id, status=Expense.PENDING)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                notes = request.POST.get('notes', '').strip()
                
                # Update status
                expense.status = Expense.REJECTED
                expense.save(update_fields=['status', 'updated_at'])
                
                # Use update_or_create to prevent IntegrityError on re-submission/race condition
                ExpenseApproval.objects.update_or_create(
                    expense=expense,
                    defaults={
                        'approved_by': request.user,
                        'status': 'rejected',
                        'notes': notes or 'Rejected by approver',
                    }
                )
                
                ActivityLog.log(
                    user=request.user, action=ActivityLog.ACTION_UPDATE,
                    model_name='Expense', object_id=str(expense.id),
                    description=f'Rejected expense: {expense.description} — GH₵{expense.amount:,.2f}',
                )
                
            messages.success(request, 'Expense rejected.')
        except Exception as e:
            # Provide more detailed error info
            messages.error(request, f'Rejection failed: {str(e)}')
            
    return redirect('approvals')
