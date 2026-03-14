"""
===========================================
General Ledger App — API Views
===========================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from .models import ChartOfAccount, JournalEntry
from .serializers import (
    ChartOfAccountSerializer,
    JournalEntrySerializer,
    JournalEntryCreateSerializer,
)
from .services import create_journal_entry, post_journal_entry, generate_trial_balance
from apps.users.permissions import IsAccountantOrAbove, CanViewReports


class ChartOfAccountViewSet(viewsets.ModelViewSet):
    """
    CRUD for Chart of Accounts.
    GET    /api/v1/gl/accounts/       — List all accounts
    POST   /api/v1/gl/accounts/       — Create new account
    GET    /api/v1/gl/accounts/{id}/   — Account detail with balance
    PUT    /api/v1/gl/accounts/{id}/   — Update account
    DELETE /api/v1/gl/accounts/{id}/   — Deactivate account
    """
    queryset = ChartOfAccount.objects.all()
    serializer_class = ChartOfAccountSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
    filterset_fields = ['account_type', 'is_active']
    search_fields = ['code', 'name']

    def perform_destroy(self, instance):
        """Soft delete: deactivate instead of deleting."""
        instance.is_active = False
        instance.save()


class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    CRUD for Journal Entries with double-entry enforcement.
    GET    /api/v1/gl/journal-entries/             — List all entries
    POST   /api/v1/gl/journal-entries/             — Create entry with lines
    GET    /api/v1/gl/journal-entries/{id}/         — Entry detail with lines
    POST   /api/v1/gl/journal-entries/{id}/post/   — Post (finalize) entry
    """
    queryset = JournalEntry.objects.select_related(
        'created_by', 'posted_by'
    ).prefetch_related('lines__account').all()
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
    filterset_fields = ['status', 'date']
    search_fields = ['entry_number', 'description', 'reference']

    def create(self, request, *args, **kwargs):
        """
        Create a journal entry with all lines in one request.
        Uses the service layer for double-entry validation.
        """
        serializer = JournalEntryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            entry = create_journal_entry(
                user=request.user,
                date=serializer.validated_data['date'],
                description=serializer.validated_data['description'],
                lines_data=serializer.validated_data['lines'],
                reference=serializer.validated_data.get('reference', ''),
            )
            return Response(
                JournalEntrySerializer(entry).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e.message if hasattr(e, 'message') else e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='post')
    def post_entry(self, request, pk=None):
        """
        POST /api/v1/gl/journal-entries/{id}/post/
        Finalize a draft journal entry. Irreversible.
        """
        try:
            entry = post_journal_entry(entry_id=pk, user=request.user)
            return Response(
                JournalEntrySerializer(entry).data,
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {'error': str(e.message if hasattr(e, 'message') else e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TrialBalanceView(viewsets.ViewSet):
    """
    GET /api/v1/gl/trial-balance/
    Auto-generated trial balance from posted journal entries.
    Optional query param: ?as_of_date=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, CanViewReports]

    def list(self, request):
        from datetime import datetime
        as_of_date_str = request.query_params.get('as_of_date')
        as_of_date = None
        if as_of_date_str:
            try:
                as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        trial_balance = generate_trial_balance(as_of_date=as_of_date)
        return Response(trial_balance)
