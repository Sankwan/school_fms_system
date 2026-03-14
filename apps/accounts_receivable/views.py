"""Accounts Receivable App — API Views."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from .models import Student, Invoice, Payment, StudentLedger, LateFeeRule
from .serializers import (
    StudentSerializer, InvoiceSerializer, PaymentSerializer,
    StudentLedgerSerializer, LateFeeRuleSerializer, RecordPaymentSerializer,
)
from .services import create_invoice, record_payment, calculate_late_fees, get_student_ledger
from apps.users.permissions import IsAccountantOrAbove, IsAdministrator


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
    search_fields = ['student_id', 'first_name', 'last_name', 'email']
    filterset_fields = ['is_active', 'program', 'year_level']

    @action(detail=True, methods=['get'], url_path='ledger')
    def student_ledger(self, request, pk=None):
        """GET /api/v1/ar/students/{id}/ledger/ — Student financial ledger."""
        ledger = get_student_ledger(student_id=pk)
        return Response(ledger)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related('student', 'created_by').prefetch_related('payments').all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
    filterset_fields = ['status', 'student', 'academic_year']
    search_fields = ['invoice_number', 'description']

    def perform_create(self, serializer):
        # Use service layer for creation with ledger entry
        data = serializer.validated_data
        create_invoice(
            user=self.request.user,
            student_id=data['student'].id,
            description=data['description'],
            amount=data['amount'],
            due_date=data['due_date'],
            academic_year=data['academic_year'],
            term=data.get('term', ''),
            late_fee_rule_id=data.get('late_fee_rule', {}).get('id') if data.get('late_fee_rule') else None,
        )

    @action(detail=True, methods=['post'], url_path='record-payment')
    def record_payment_action(self, request, pk=None):
        """POST /api/v1/ar/invoices/{id}/record-payment/"""
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = record_payment(
                user=request.user,
                invoice_id=pk,
                **serializer.validated_data
            )
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OutstandingBalancesView(viewsets.ViewSet):
    """GET /api/v1/ar/outstanding/ — Outstanding balances report."""
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]

    def list(self, request):
        students = Student.objects.filter(is_active=True)
        data = []
        for student in students:
            outstanding = student.total_outstanding
            if outstanding > 0:
                data.append({
                    'student_id': student.student_id,
                    'name': student.full_name,
                    'program': student.program,
                    'outstanding': float(outstanding),
                })
        data.sort(key=lambda x: x['outstanding'], reverse=True)
        return Response(data)


class CalculateLateFeesView(viewsets.ViewSet):
    """POST /api/v1/ar/calculate-late-fees/ — Trigger late fee calculation."""
    permission_classes = [IsAuthenticated, IsAdministrator]

    def create(self, request):
        result = calculate_late_fees()
        return Response(result)


class LateFeeRuleViewSet(viewsets.ModelViewSet):
    queryset = LateFeeRule.objects.all()
    serializer_class = LateFeeRuleSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
