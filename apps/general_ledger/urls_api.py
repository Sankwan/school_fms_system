"""General Ledger App — API URL Configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.ChartOfAccountViewSet, basename='account')
router.register(r'journal-entries', views.JournalEntryViewSet, basename='journal-entry')
router.register(r'trial-balance', views.TrialBalanceView, basename='trial-balance')

urlpatterns = [
    path('', include(router.urls)),
]
