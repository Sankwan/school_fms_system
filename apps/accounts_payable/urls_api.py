"""Accounts Payable App — API URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vendors', views.VendorViewSet, basename='vendor')
router.register(r'categories', views.ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'recurring', views.RecurringExpenseViewSet, basename='recurring')

urlpatterns = [
    path('', include(router.urls)),
    path('recurring/process/', views.ProcessRecurringView.as_view({'post': 'create'}), name='process-recurring'),
]
