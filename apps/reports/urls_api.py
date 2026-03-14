"""Reports App — API URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'periods', views.AcademicPeriodViewSet, basename='period')
router.register(r'budgets', views.BudgetViewSet, basename='budget')

urlpatterns = [
    path('', include(router.urls)),
    path('balance-sheet/', views.BalanceSheetView.as_view(), name='api-balance-sheet'),
    path('income-statement/', views.IncomeStatementView.as_view(), name='api-income-statement'),
    path('cash-flow/', views.CashFlowView.as_view(), name='api-cash-flow'),
    path('budget-vs-actual/', views.BudgetVsActualView.as_view(), name='api-budget-vs-actual'),
    path('<str:report_type>/export/<str:export_format>/', views.ExportReportView.as_view(), name='api-export-report'),
]
