"""General Ledger App — Web URL Configuration."""

from django.urls import path
from . import views_web

urlpatterns = [
    path('chart-of-accounts/', views_web.chart_of_accounts_view, name='chart-of-accounts'),
    path('journal-entries/', views_web.journal_entries_view, name='journal-entries'),
    path('journal-entries/new/', views_web.journal_entry_form_view, name='journal-entry-create'),
    path('journal-entries/<int:entry_id>/post/', views_web.journal_entry_post_view, name='journal-entry-post'),
    path('trial-balance/', views_web.trial_balance_view, name='trial-balance'),
]
