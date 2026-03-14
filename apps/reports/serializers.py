"""Reports App — Serializers."""

from rest_framework import serializers
from .models import AcademicPeriod, Budget


class AcademicPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = '__all__'


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    actual_spent = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    variance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    utilization_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Budget
        fields = '__all__'
