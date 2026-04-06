"""Accounts Payable App — Web URLs."""

from django.urls import path
from . import views_web

urlpatterns = [
    # Vendors
    path('vendors/', views_web.vendors_view, name='vendors'),
    path('vendors/new/', views_web.vendor_form_view, name='vendor-create'),
    path('vendors/<int:vendor_id>/edit/', views_web.vendor_form_view, name='vendor-edit'),
    path('vendors/<int:vendor_id>/delete/', views_web.vendor_delete_view, name='vendor-delete'),
    # Expenses
    path('expenses/', views_web.expenses_view, name='expenses'),
    path('expenses/new/', views_web.expense_form_view, name='expense-create'),
    # Approvals
    path('approvals/', views_web.approvals_view, name='approvals'),
    path('approvals/<int:expense_id>/approve/', views_web.expense_approve_view, name='expense-approve-web'),
    path('approvals/<int:expense_id>/reject/', views_web.expense_reject_view, name='expense-reject-web'),
]
