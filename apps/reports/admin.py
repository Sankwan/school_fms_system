"""Reports App — Django Admin."""

from django.contrib import admin
from .models import AcademicPeriod, Budget


@admin.register(AcademicPeriod)
class AcademicPeriodAdmin(admin.ModelAdmin):
    list_display = ['year', 'term', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['category', 'academic_period', 'amount', 'period_type']
    list_filter = ['academic_period', 'period_type']
