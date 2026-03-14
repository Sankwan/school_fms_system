"""
===========================================
Seed Data Management Command
===========================================
Creates demo data for all modules.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from apps.users.models import CustomUser, Role
from apps.general_ledger.models import ChartOfAccount, JournalEntry, JournalEntryLine
from apps.accounts_receivable.models import Student, Invoice, Payment, LateFeeRule
from apps.accounts_payable.models import Vendor, ExpenseCategory, Expense
from apps.reports.models import AcademicPeriod, Budget


class Command(BaseCommand):
    help = 'Seed the database with demo data for all modules'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        self._create_roles()
        self._create_users()
        self._create_chart_of_accounts()
        self._create_academic_periods()
        self._create_students()
        self._create_late_fee_rules()
        self._create_vendors()
        self._create_expense_categories()
        self._create_sample_data()

        self.stdout.write(self.style.SUCCESS('✅ Database seeded successfully!'))

    def _create_roles(self):
        """Create the 5 system roles with appropriate permissions."""
        roles_config = [
            {
                'name': Role.ADMINISTRATOR,
                'description': 'Full system access',
                'can_manage_users': True, 'can_manage_ledger': True,
                'can_post_entries': True, 'can_manage_receivables': True,
                'can_manage_payables': True, 'can_approve_expenses': True,
                'can_view_reports': True, 'can_export_reports': True,
                'can_manage_budgets': True, 'can_view_audit_log': True,
                'can_view_student_ledger': True,
            },
            {
                'name': Role.ACCOUNTANT,
                'description': 'Financial data management',
                'can_manage_ledger': True, 'can_post_entries': True,
                'can_manage_receivables': True, 'can_manage_payables': True,
                'can_view_reports': True, 'can_export_reports': True,
                'can_manage_budgets': True,
                'can_view_student_ledger': True,
            },
            {
                'name': Role.FINANCE_OFFICER,
                'description': 'Financial oversight and approval',
                'can_manage_ledger': True,
                'can_manage_receivables': True, 'can_manage_payables': True,
                'can_approve_expenses': True, 'can_view_reports': True,
                'can_export_reports': True, 'can_manage_budgets': True,
                'can_view_student_ledger': True,
            },
            {
                'name': Role.AUDITOR,
                'description': 'Read-only access for audit purposes',
                'can_view_reports': True, 'can_export_reports': True,
                'can_view_audit_log': True,
                'can_view_student_ledger': True,
            },
            {
                'name': Role.TEACHER,
                'description': 'Limited view for student financial data',
                'can_view_student_ledger': True,
            },
        ]

        for config in roles_config:
            Role.objects.update_or_create(
                name=config.pop('name'),
                defaults=config,
            )
        self.stdout.write('  ✓ Roles created')

    def _create_users(self):
        """Create demo users for each role."""
        admin_role = Role.objects.get(name=Role.ADMINISTRATOR)

        # Create superuser
        if not CustomUser.objects.filter(email='admin@school.edu').exists():
            admin = CustomUser.objects.create_superuser(
                email='admin@school.edu',
                username='admin',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                role=admin_role,
            )

        demo_users = [
            ('accountant@school.edu', 'accountant', 'Jane', 'Smith', Role.ACCOUNTANT),
            ('finance@school.edu', 'finance', 'Michael', 'Johnson', Role.FINANCE_OFFICER),
            ('auditor@school.edu', 'auditor', 'Sarah', 'Williams', Role.AUDITOR),
            ('teacher@school.edu', 'teacher', 'David', 'Brown', Role.TEACHER),
        ]

        for email, username, first, last, role_name in demo_users:
            if not CustomUser.objects.filter(email=email).exists():
                role = Role.objects.get(name=role_name)
                CustomUser.objects.create_user(
                    email=email,
                    username=username,
                    password='demo123',
                    first_name=first,
                    last_name=last,
                    role=role,
                )
        self.stdout.write('  ✓ Users created')

    def _create_chart_of_accounts(self):
        """Create standard chart of accounts for a school."""
        accounts = [
            # ASSETS (1000-1999)
            ('1000', 'Cash', ChartOfAccount.ASSET, 'debit'),
            ('1010', 'Petty Cash', ChartOfAccount.ASSET, 'debit'),
            ('1100', 'Bank Account - Main', ChartOfAccount.ASSET, 'debit'),
            ('1200', 'Accounts Receivable', ChartOfAccount.ASSET, 'debit'),
            ('1300', 'Prepaid Expenses', ChartOfAccount.ASSET, 'debit'),
            ('1500', 'Equipment', ChartOfAccount.ASSET, 'debit'),
            ('1600', 'Furniture & Fixtures', ChartOfAccount.ASSET, 'debit'),
            # LIABILITIES (2000-2999)
            ('2000', 'Accounts Payable', ChartOfAccount.LIABILITY, 'credit'),
            ('2100', 'Accrued Expenses', ChartOfAccount.LIABILITY, 'credit'),
            ('2200', 'Unearned Revenue', ChartOfAccount.LIABILITY, 'credit'),
            ('2500', 'Long-term Loans', ChartOfAccount.LIABILITY, 'credit'),
            # EQUITY (3000-3999)
            ('3000', 'Opening Balance Equity', ChartOfAccount.EQUITY, 'credit'),
            ('3100', 'Retained Earnings', ChartOfAccount.EQUITY, 'credit'),
            # INCOME (4000-4999)
            ('4000', 'Tuition Fee Income', ChartOfAccount.INCOME, 'credit'),
            ('4100', 'Registration Fee Income', ChartOfAccount.INCOME, 'credit'),
            ('4200', 'Examination Fee Income', ChartOfAccount.INCOME, 'credit'),
            ('4300', 'Library Fee Income', ChartOfAccount.INCOME, 'credit'),
            ('4400', 'Laboratory Fee Income', ChartOfAccount.INCOME, 'credit'),
            ('4500', 'Other Income', ChartOfAccount.INCOME, 'credit'),
            ('4600', 'Government Grants', ChartOfAccount.INCOME, 'credit'),
            # EXPENSES (5000-5999)
            ('5000', 'Salaries & Wages', ChartOfAccount.EXPENSE, 'debit'),
            ('5100', 'Teaching Materials', ChartOfAccount.EXPENSE, 'debit'),
            ('5200', 'Utilities', ChartOfAccount.EXPENSE, 'debit'),
            ('5300', 'Rent', ChartOfAccount.EXPENSE, 'debit'),
            ('5400', 'Maintenance & Repairs', ChartOfAccount.EXPENSE, 'debit'),
            ('5500', 'Insurance', ChartOfAccount.EXPENSE, 'debit'),
            ('5600', 'Office Supplies', ChartOfAccount.EXPENSE, 'debit'),
            ('5700', 'Transport', ChartOfAccount.EXPENSE, 'debit'),
            ('5800', 'Depreciation', ChartOfAccount.EXPENSE, 'debit'),
            ('5900', 'Miscellaneous Expenses', ChartOfAccount.EXPENSE, 'debit'),
        ]

        for code, name, acc_type, bal_type in accounts:
            ChartOfAccount.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'account_type': acc_type,
                    'balance_type': bal_type,
                }
            )
        self.stdout.write('  ✓ Chart of Accounts created')

    def _create_academic_periods(self):
        """Create academic periods."""
        AcademicPeriod.objects.get_or_create(
            year='2025/2026', term='Semester 1',
            defaults={
                'start_date': date(2025, 9, 1),
                'end_date': date(2026, 1, 31),
                'is_current': True,
            }
        )
        AcademicPeriod.objects.get_or_create(
            year='2025/2026', term='Semester 2',
            defaults={
                'start_date': date(2026, 2, 1),
                'end_date': date(2026, 6, 30),
            }
        )
        self.stdout.write('  ✓ Academic periods created')

    def _create_students(self):
        """Create demo students."""
        students = [
            ('STU-2025-001', 'Kwame', 'Asante', 'Computer Science', 2),
            ('STU-2025-002', 'Ama', 'Mensah', 'Business Administration', 1),
            ('STU-2025-003', 'Yaw', 'Boateng', 'Engineering', 3),
            ('STU-2025-004', 'Efua', 'Owusu', 'Nursing', 2),
            ('STU-2025-005', 'Kofi', 'Adjei', 'Accounting', 1),
        ]
        for sid, first, last, program, year in students:
            Student.objects.get_or_create(
                student_id=sid,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'program': program,
                    'year_level': year,
                    'enrollment_date': date(2025, 9, 1),
                }
            )
        self.stdout.write('  ✓ Students created')

    def _create_late_fee_rules(self):
        """Create late fee rules."""
        LateFeeRule.objects.get_or_create(
            name='Standard Late Fee (5%)',
            defaults={
                'grace_period_days': 14,
                'rate_type': 'percentage',
                'rate_value': Decimal('5.00'),
                'max_fee': Decimal('500.00'),
            }
        )
        self.stdout.write('  ✓ Late fee rules created')

    def _create_vendors(self):
        """Create demo vendors."""
        vendors = [
            ('ABC Supplies Ltd', 'John Doe', 'john@abcsupplies.com', '020-123-4567'),
            ('City Power Company', 'Customer Service', 'billing@citypower.com', '030-555-0100'),
            ('National Books Store', 'Mary Smith', 'orders@nationalbooks.com', '024-987-6543'),
            ('Fresh Foods Catering', 'Chef Adams', 'orders@freshfoods.com', '027-111-2222'),
        ]
        for name, contact, email, phone in vendors:
            Vendor.objects.get_or_create(
                name=name,
                defaults={
                    'contact_person': contact,
                    'email': email,
                    'phone': phone,
                }
            )
        self.stdout.write('  ✓ Vendors created')

    def _create_expense_categories(self):
        """Create expense categories."""
        categories = [
            ('EXP-SAL', 'Salaries & Wages'),
            ('EXP-UTL', 'Utilities'),
            ('EXP-SUP', 'Office Supplies'),
            ('EXP-MAT', 'Teaching Materials'),
            ('EXP-MNT', 'Maintenance'),
            ('EXP-TRN', 'Transport'),
            ('EXP-MSC', 'Miscellaneous'),
        ]
        for code, name in categories:
            ExpenseCategory.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )
        self.stdout.write('  ✓ Expense categories created')

    def _create_sample_data(self):
        """Create sample transactions for the demo."""
        admin = CustomUser.objects.get(email='admin@school.edu')

        # Sample journal entry (opening balance)
        if not JournalEntry.objects.exists():
            entry = JournalEntry.objects.create(
                date=date(2025, 9, 1),
                description='Opening balance - Cash in Bank',
                reference='OPENING',
                status=JournalEntry.POSTED,
                created_by=admin,
                posted_by=admin,
                posted_at=timezone.now(),
            )
            cash_account = ChartOfAccount.objects.get(code='1100')
            equity_account = ChartOfAccount.objects.get(code='3000')

            JournalEntryLine.objects.create(
                journal_entry=entry,
                account=cash_account,
                debit=Decimal('100000.00'),
                credit=Decimal('0.00'),
                description='Opening cash balance',
            )
            JournalEntryLine.objects.create(
                journal_entry=entry,
                account=equity_account,
                debit=Decimal('0.00'),
                credit=Decimal('100000.00'),
                description='Opening equity',
            )

        # Create a sample invoice
        if not Invoice.objects.exists():
            student = Student.objects.first()
            late_fee_rule = LateFeeRule.objects.first()
            Invoice.objects.create(
                student=student,
                description='Tuition Fee - Semester 1, 2025/2026',
                amount=Decimal('5000.00'),
                due_date=date(2025, 10, 15),
                academic_year='2025/2026',
                term='Semester 1',
                late_fee_rule=late_fee_rule,
                created_by=admin,
            )

        self.stdout.write('  ✓ Sample transactions created')
