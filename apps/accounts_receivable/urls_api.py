"""Accounts Receivable App — API URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'outstanding', views.OutstandingBalancesView, basename='outstanding')
router.register(r'late-fee-rules', views.LateFeeRuleViewSet, basename='late-fee-rule')

urlpatterns = [
    path('', include(router.urls)),
    path('calculate-late-fees/', views.CalculateLateFeesView.as_view({'post': 'create'}), name='calculate-late-fees'),
]
