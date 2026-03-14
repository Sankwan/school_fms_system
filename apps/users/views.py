"""
===========================================
Users App — API Views
===========================================
REST API endpoints for authentication, user management,
and audit log access.
"""

from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend

from .models import CustomUser, Role, ActivityLog
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserProfileSerializer,
    ActivityLogSerializer,
    RoleSerializer,
)
from .permissions import IsAdministrator, CanViewAuditLog


# -----------------------------------------------
# Authentication Endpoints
# -----------------------------------------------

class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Authenticate user and return JWT access + refresh tokens.
    Also returns user info (id, email, role) in the response body.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklist the refresh token to log out the user.
    Expects: { "refresh": "<refresh_token>" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log the logout event
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.ACTION_LOGOUT,
                description='User logged out via API.',
                request=request,
            )

            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# -----------------------------------------------
# User Profile
# -----------------------------------------------

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/auth/profile/   — Get current user's profile
    PUT /api/v1/auth/profile/   — Update profile (name, phone, etc.)
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# -----------------------------------------------
# User Management (Admin only)
# -----------------------------------------------

class UserViewSet(viewsets.ModelViewSet):
    """
    Admin-only user management CRUD.
    GET    /api/v1/admin/users/      — List all users
    POST   /api/v1/admin/users/      — Create a user
    GET    /api/v1/admin/users/{id}/  — Get user details
    PUT    /api/v1/admin/users/{id}/  — Update user
    DELETE /api/v1/admin/users/{id}/  — Deactivate user
    """
    queryset = CustomUser.objects.select_related('role').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active']

    def perform_destroy(self, instance):
        """Soft delete: deactivate instead of deleting."""
        instance.is_active = False
        instance.save()

        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.ACTION_DELETE,
            model_name='CustomUser',
            object_id=str(instance.id),
            description=f'Deactivated user: {instance.email}',
            request=self.request,
        )


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/admin/roles/ — List all available roles and their permissions.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]


# -----------------------------------------------
# Audit Log (Admin + Auditor)
# -----------------------------------------------

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/admin/audit-log/ — View system activity log.
    Supports filtering by user, action, date range.
    """
    queryset = ActivityLog.objects.select_related('user').all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, CanViewAuditLog]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'user', 'model_name']


# -----------------------------------------------
# Dashboard Stats
# -----------------------------------------------

class DashboardStatsView(APIView):
    """
    GET /api/v1/admin/dashboard-stats/
    Returns summary statistics for the dashboard.
    Data returned depends on the user's role.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.accounts_receivable.models import Invoice, Student
        from apps.accounts_payable.models import Expense
        from apps.general_ledger.models import JournalEntry
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        stats = {}

        # Stats visible to all authenticated users
        stats['total_students'] = Student.objects.count()

        # Financial stats (not for teachers)
        if not request.user.is_teacher():
            stats['total_invoices'] = Invoice.objects.count()
            stats['outstanding_amount'] = float(
                Invoice.objects.filter(
                    status__in=['unpaid', 'partial', 'overdue']
                ).aggregate(
                    total=Sum('amount') - Sum('amount_paid')
                )['total'] or 0
            )
            stats['pending_expenses'] = Expense.objects.filter(
                status='pending'
            ).count()
            stats['recent_journal_entries'] = JournalEntry.objects.filter(
                date__gte=thirty_days_ago
            ).count()

        return Response(stats)
