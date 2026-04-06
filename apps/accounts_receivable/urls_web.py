"""Accounts Receivable App — Web URLs."""

from django.urls import path
from . import views_web

urlpatterns = [
    # Students
    path('students/', views_web.students_view, name='students'),
    path('students/new/', views_web.student_form_view, name='student-create'),
    path('students/<int:student_id>/edit/', views_web.student_form_view, name='student-edit'),
    path('students/<int:student_id>/delete/', views_web.student_delete_view, name='student-delete'),
    path('students/<int:student_id>/ledger/', views_web.student_ledger_view, name='student-ledger'),
    # Invoices
    path('invoices/', views_web.invoices_view, name='invoices'),
    path('invoices/new/', views_web.invoice_form_view, name='invoice-create'),
    path('invoices/<int:invoice_id>/print/', views_web.invoice_print_view, name='invoice-print'),
    # Payments
    path('payments/', views_web.payments_view, name='payments'),
    path('payments/new/', views_web.payment_form_view, name='payment-create'),
]
