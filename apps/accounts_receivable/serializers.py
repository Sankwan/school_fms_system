"""Accounts Receivable App — Serializers."""

from rest_framework import serializers
from .models import Student, Invoice, Payment, StudentLedger, LateFeeRule


class StudentSerializer(serializers.ModelSerializer):
    total_outstanding = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Student
        fields = '__all__'


class LateFeeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LateFeeRule
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    received_by_name = serializers.CharField(
        source='received_by.get_full_name', read_only=True
    )

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['received_by']


class InvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    outstanding_balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'amount_paid', 'late_fee', 'status', 'created_by']


class StudentLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentLedger
        fields = '__all__'


class RecordPaymentSerializer(serializers.Serializer):
    """Serializer for the record-payment action."""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHOD_CHOICES)
    payment_date = serializers.DateField()
    reference = serializers.CharField(required=False, default='')
    notes = serializers.CharField(required=False, default='')
