"""Accounts Payable App — API Views."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from .models import Vendor, Expense, ExpenseCategory, RecurringSchedule
from .serializers import (
    VendorSerializer, ExpenseSerializer, ExpenseCategorySerializer,
    RecurringScheduleSerializer,
)
from .services import approve_expense, reject_expense, process_recurring_expenses
from apps.users.permissions import IsAccountantOrAbove, CanApproveExpenses, IsAdministrator


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
    search_fields = ['name', 'contact_person', 'email']
    filterset_fields = ['is_active']


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related(
        'vendor', 'category', 'submitted_by'
    ).prefetch_related('approval').all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
    filterset_fields = ['status', 'vendor', 'category', 'is_recurring']
    search_fields = ['description']

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='approve',
            permission_classes=[IsAuthenticated, CanApproveExpenses])
    def approve(self, request, pk=None):
        """POST /api/v1/ap/expenses/{id}/approve/"""
        try:
            notes = request.data.get('notes', '')
            expense = approve_expense(pk, request.user, notes)
            return Response(ExpenseSerializer(expense).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reject',
            permission_classes=[IsAuthenticated, CanApproveExpenses])
    def reject(self, request, pk=None):
        """POST /api/v1/ap/expenses/{id}/reject/"""
        try:
            notes = request.data.get('notes', '')
            expense = reject_expense(pk, request.user, notes)
            return Response(ExpenseSerializer(expense).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecurringExpenseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RecurringSchedule.objects.select_related('expense').all()
    serializer_class = RecurringScheduleSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]


class ProcessRecurringView(viewsets.ViewSet):
    """POST /api/v1/ap/recurring/process/ — Trigger recurring expense processing."""
    permission_classes = [IsAuthenticated, IsAdministrator]

    def create(self, request):
        result = process_recurring_expenses()
        return Response(result)
