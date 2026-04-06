"""Reports App — Web URLs."""

from django.urls import path
from . import views_web

urlpatterns = [
    path('', views_web.dashboard_view, name='dashboard'),
    path('reports/balance-sheet/', views_web.balance_sheet_view, name='balance-sheet'),
    path('reports/income-statement/', views_web.income_statement_view, name='income-statement'),
    path('reports/audit-log/', views_web.audit_log_view, name='audit-log'),
    path('reports/<str:report_type>/export/<str:export_format>/', views_web.export_view, name='export-report'),
]
