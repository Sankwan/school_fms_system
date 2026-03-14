"""Reports App — API Views."""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AcademicPeriod, Budget
from .serializers import AcademicPeriodSerializer, BudgetSerializer
from .services import (
    generate_balance_sheet, generate_income_statement,
    generate_cash_flow, generate_budget_vs_actual,
)
from .export import export_report_to_pdf, export_report_to_excel
from apps.users.permissions import CanViewReports, CanExportReports, IsAccountantOrAbove
from apps.users.models import ActivityLog


class AcademicPeriodViewSet(viewsets.ModelViewSet):
    queryset = AcademicPeriod.objects.all()
    serializer_class = AcademicPeriodSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.select_related('category', 'academic_period').all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAbove]
    filterset_fields = ['academic_period', 'category']


class BalanceSheetView(APIView):
    """GET /api/v1/reports/balance-sheet/"""
    permission_classes = [IsAuthenticated, CanViewReports]

    def get(self, request):
        as_of_date = request.query_params.get('as_of_date')
        report = generate_balance_sheet(as_of_date=as_of_date)
        return Response(report)


class IncomeStatementView(APIView):
    """GET /api/v1/reports/income-statement/"""
    permission_classes = [IsAuthenticated, CanViewReports]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        report = generate_income_statement(start_date=start_date, end_date=end_date)
        return Response(report)


class CashFlowView(APIView):
    """GET /api/v1/reports/cash-flow/"""
    permission_classes = [IsAuthenticated, CanViewReports]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        report = generate_cash_flow(start_date=start_date, end_date=end_date)
        return Response(report)


class BudgetVsActualView(APIView):
    """GET /api/v1/reports/budget-vs-actual/"""
    permission_classes = [IsAuthenticated, CanViewReports]

    def get(self, request):
        period_id = request.query_params.get('period_id')
        report = generate_budget_vs_actual(academic_period_id=period_id)
        return Response(report)


class ExportReportView(APIView):
    """
    GET /api/v1/reports/{type}/export/pdf/
    GET /api/v1/reports/{type}/export/excel/
    """
    permission_classes = [IsAuthenticated, CanExportReports]

    def get(self, request, report_type, export_format):
        # Generate the report data
        generators = {
            'balance-sheet': generate_balance_sheet,
            'income-statement': generate_income_statement,
            'cash-flow': generate_cash_flow,
            'budget-vs-actual': generate_budget_vs_actual,
        }

        generator = generators.get(report_type)
        if not generator:
            return Response({'error': 'Invalid report type.'}, status=status.HTTP_400_BAD_REQUEST)

        report_data = generator()

        # Log the export
        ActivityLog.log(
            user=request.user,
            action=ActivityLog.ACTION_EXPORT,
            model_name='Report',
            description=f'Exported {report_type} as {export_format}',
            request=request,
        )

        report_type_key = report_type.replace('-', '_')

        if export_format == 'pdf':
            return export_report_to_pdf(report_data, report_type_key)
        elif export_format == 'excel':
            return export_report_to_excel(report_data, report_type_key)
        else:
            return Response({'error': 'Format must be pdf or excel.'}, status=status.HTTP_400_BAD_REQUEST)
