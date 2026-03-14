"""Accounts Payable App — Serializers."""

from rest_framework import serializers
from .models import Vendor, Expense, ExpenseCategory, ExpenseApproval, RecurringSchedule


class VendorSerializer(serializers.ModelSerializer):
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


class ExpenseApprovalSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = ExpenseApproval
        fields = '__all__'
        read_only_fields = ['approved_by', 'approved_at']


class RecurringScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringSchedule
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True, default=None)
    category_name = serializers.CharField(source='category.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    approval = ExpenseApprovalSerializer(read_only=True)
    recurring_schedule = RecurringScheduleSerializer(read_only=True)

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['status', 'submitted_by']
