"""
===========================================
General Ledger App — Serializers
===========================================
"""

from rest_framework import serializers
from .models import ChartOfAccount, JournalEntry, JournalEntryLine


class ChartOfAccountSerializer(serializers.ModelSerializer):
    """Serializer for Chart of Accounts with computed balance."""

    balance = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    parent_name = serializers.CharField(
        source='parent.name', read_only=True, default=None
    )
    children = serializers.SerializerMethodField()

    class Meta:
        model = ChartOfAccount
        fields = [
            'id', 'code', 'name', 'description', 'account_type',
            'balance_type', 'parent', 'parent_name', 'children',
            'is_active', 'balance', 'created_at',
        ]

    def get_children(self, obj):
        """Return direct child accounts."""
        children = obj.children.filter(is_active=True)
        return ChartOfAccountSerializer(children, many=True).data


class JournalEntryLineSerializer(serializers.ModelSerializer):
    """Serializer for individual journal entry lines."""

    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = JournalEntryLine
        fields = [
            'id', 'account', 'account_code', 'account_name',
            'description', 'debit', 'credit',
        ]


class JournalEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for Journal Entries with nested lines.
    Supports creating entries with lines in a single request.
    """

    lines = JournalEntryLineSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )
    posted_by_name = serializers.CharField(
        source='posted_by.get_full_name', read_only=True, default=None
    )
    total_debit = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    total_credit = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    is_balanced = serializers.BooleanField(read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'entry_number', 'date', 'description', 'reference',
            'status', 'lines', 'created_by', 'created_by_name',
            'posted_by', 'posted_by_name', 'posted_at',
            'total_debit', 'total_credit', 'is_balanced',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'entry_number', 'status', 'created_by', 'posted_by', 'posted_at',
        ]


class JournalEntryCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a journal entry with lines.
    Uses the service layer for double-entry enforcement.
    """

    date = serializers.DateField()
    description = serializers.CharField()
    reference = serializers.CharField(required=False, default='')
    lines = serializers.ListField(
        child=serializers.DictField(),
        min_length=2,
        help_text='List of lines. Each: {account_id, debit, credit, description}'
    )


class TrialBalanceSerializer(serializers.Serializer):
    """Serializer for trial balance report output."""

    as_of_date = serializers.DateField()
    accounts = serializers.ListField()
    total_debit = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_credit = serializers.DecimalField(max_digits=15, decimal_places=2)
    is_balanced = serializers.BooleanField()
