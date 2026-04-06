# 🏫 School Financial Management System (FMS)

**Enterprise-grade financial management for Senior High Schools and Universities.**

Built with Django 5.x, MySQL 8.x, Django REST Framework, and a modern responsive dark-themed UI.

---

## ✨ Features

### Core Modules
- **📒 General Ledger** — Chart of Accounts (hierarchical), Journal Entries (double-entry enforcement), Trial Balance
- **🎓 Accounts Receivable** — Student invoicing, payment tracking, student ledger, configurable late fees
- **💰 Accounts Payable** — Vendor management, expenses with approval workflow, recurring expenses
- **📊 Reports & Budgets** — Balance Sheet, Income Statement, Cash Flow, Budget vs Actual with PDF/Excel export

### Security & Compliance
- **🔐 JWT Authentication** — Secure token-based API access
- **👥 Role-Based Access Control** — 5 roles (Admin, Accountant, Finance Officer, Auditor, Teacher) with 11 granular permissions
- **📋 Audit Trail** — Complete activity logging with IP tracking
- **🔒 Account Lockout** — After 5 failed login attempts
- **🛡️ CSRF Protection, XSS Prevention, Clickjacking Protection**

### Modern UI
- Dark glassmorphism theme with smooth animations
- Interactive dashboard with Chart.js (income trends, expense distribution)
- KPI cards, data tables, and responsive design
- Role-aware sidebar navigation

---

## 🏗️ Architecture

```
┌───────────────────────────────┐
│   Presentation Layer (UI)     │  Django Templates + CSS + JS + Chart.js
├───────────────────────────────┤
│   Application Layer (API)     │  Django REST Framework + JWT + RBAC
├───────────────────────────────┤
│   Data Layer (Database)       │  MySQL 8.x (ACID compliant)
└───────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MySQL 8.x
- pip

### 1. Clone and Install

```bash
cd school_fms
python -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Create MySQL Database

```sql
CREATE DATABASE school_fms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Demo Data

```bash
python manage.py seed_data
```

This creates:
- 5 system roles with configured permissions
- Demo users (admin@school.edu / admin123)
- 30 chart of accounts entries
- Students, vendors, expense categories
- Academic periods and sample transactions

### 6. Run the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/dashboard/** to access the system.

---

## 📁 Project Structure

```
school_fms/
├── config/                    # Project configuration
│   ├── settings/
│   │   ├── base.py            # Shared settings
│   │   ├── development.py     # Dev overrides
│   │   └── production.py      # Production security
│   ├── urls.py                # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/                 # Auth, RBAC, Audit
│   ├── general_ledger/        # GL, Journal Entries
│   ├── accounts_receivable/   # Students, Invoices
│   ├── accounts_payable/      # Vendors, Expenses
│   └── reports/               # Reports, Budgets
├── templates/                 # HTML templates
├── static/                    # CSS, JS
├── scripts/                   # Backup utilities
├── manage.py
├── requirements.txt
└── .env.example
```

---

## 🔌 API Endpoints

All API endpoints are under `/api/v1/` and require JWT authentication.

| Module | Endpoint | Methods |
|--------|----------|---------|
| **Auth** | `/api/v1/auth/login/` | POST |
| **Auth** | `/api/v1/auth/logout/` | POST |
| **GL** | `/api/v1/gl/accounts/` | GET, POST, PUT, DELETE |
| **GL** | `/api/v1/gl/journal-entries/` | GET, POST |
| **GL** | `/api/v1/gl/journal-entries/{id}/post/` | POST |
| **GL** | `/api/v1/gl/trial-balance/` | GET |
| **AR** | `/api/v1/ar/students/` | GET, POST, PUT, DELETE |
| **AR** | `/api/v1/ar/invoices/` | GET, POST |
| **AR** | `/api/v1/ar/invoices/{id}/record-payment/` | POST |
| **AR** | `/api/v1/ar/outstanding/` | GET |
| **AP** | `/api/v1/ap/vendors/` | GET, POST, PUT, DELETE |
| **AP** | `/api/v1/ap/expenses/` | GET, POST |
| **AP** | `/api/v1/ap/expenses/{id}/approve/` | POST |
| **AP** | `/api/v1/ap/expenses/{id}/reject/` | POST |
| **Reports** | `/api/v1/reports/balance-sheet/` | GET |
| **Reports** | `/api/v1/reports/income-statement/` | GET |
| **Reports** | `/api/v1/reports/cash-flow/` | GET |
| **Reports** | `/api/v1/reports/budget-vs-actual/` | GET |
| **Reports** | `/api/v1/reports/{type}/export/{format}/` | GET |

---

## 👥 Demo Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@school.edu | admin123 | Administrator |
| accountant@school.edu | demo123 | Accountant |
<!-- | finance@school.edu | demo123 | Finance Officer | -->
| auditor@school.edu | demo123 | Auditor |
<!-- | teacher@school.edu | demo123 | Teacher | -->

---

## 🗄️ Database Backup

```bash
python scripts/backup.py
```

Backups are stored in the `backups/` directory (configurable via `BACKUP_DIR` in `.env`).

---

## 📜 License

This project is for educational and institutional use.
