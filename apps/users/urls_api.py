"""Users App — API URL Configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'roles', views.RoleViewSet, basename='role')
router.register(r'audit-log', views.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # JWT Authentication
    path('login/', views.LoginView.as_view(), name='api-login'),
    path('refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('logout/', views.LogoutView.as_view(), name='api-logout'),
    path('profile/', views.ProfileView.as_view(), name='api-profile'),

    # Dashboard Stats
    path('dashboard-stats/', views.DashboardStatsView.as_view(), name='api-dashboard-stats'),

    # Admin management (users, roles, audit log)
    path('admin/', include(router.urls)),
]
