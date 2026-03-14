# School FMS — Setup Guide

> **Hand this entire file to an AI assistant** (ChatGPT, Claude, Gemini, etc.) and say:
> *"Follow the instructions in this file to get my Django project running on my machine."*
> It contains everything needed — no guesswork required.

---

## AI PROMPT (copy-paste this to your AI assistant)

```
I have a Django project called "School FMS" (Financial Management System).
I need you to help me set it up and run it on my local machine.

Here is what you need to know:
- Framework: Django 4.2 (Python)
- Database: SQLite (for local development — no MySQL needed)
- The project uses a virtual environment (venv)
- The settings module for development is: config.settings.development
- After setup, seed the database with demo data using: python3 manage.py seed_data
- The dev server runs on: http://127.0.0.1:8000/

Please run the EXACT commands listed below in order. If any command fails,
diagnose and fix the issue before moving to the next step.

STEP 1 — Create virtual environment:
  python3 -m venv venv

STEP 2 — Activate virtual environment:
  macOS/Linux:  source venv/bin/activate
  Windows:      venv\Scripts\activate

STEP 3 — Install dependencies:
  pip install -r requirements.txt

STEP 4 — Run database migrations:
  python3 manage.py migrate

STEP 5 — Seed demo data (creates users, students, accounts, sample transactions):
  python3 manage.py seed_data

STEP 6 — Start the development server:
  python3 manage.py runserver

STEP 7 — Open browser and go to:
  http://127.0.0.1:8000/

STEP 8 — Login with:
  Email: admin@school.edu
  Password: admin123

If you get a "command not found: python3" error, try using "python" instead.
If you get a "no module named django" error, make sure the virtual environment
is activated (you should see "(venv)" at the start of your terminal prompt).
If port 8000 is in use, run: python3 manage.py runserver 8080
```

---

## MANUAL SETUP (Step-by-Step)

### Prerequisites

| Requirement | Minimum Version | Check Command |
|---|---|---|
| Python | 3.8+ | `python3 --version` |
| pip | any | `pip --version` |
| Git (optional) | any | `git --version` |

> **No MySQL, PostgreSQL, or any other database is needed for local development.** The project uses SQLite by default.

### 1. Extract the Project

```bash
# If you received a zip file:
unzip school_fms.zip
cd school_fms
```

### 2. Create & Activate Virtual Environment

```bash
# Create
python3 -m venv venv

# Activate (macOS / Linux)
source venv/bin/activate

# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat
```

You should see `(venv)` appear at the start of your terminal prompt.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you get errors about `mysqlclient`, ignore them — it's commented out in requirements.txt and not needed for local dev.

### 4. Run Migrations

```bash
python3 manage.py migrate
```

This creates the SQLite database file (`db.sqlite3`) with all tables.

### 5. Seed Demo Data

```bash
python3 manage.py seed_data
```

This creates:
- 5 user roles (Administrator, Accountant, Finance Officer, Auditor, Teacher)
- 5 demo user accounts
- 5 demo students
- 4 demo vendors
- Chart of accounts (28 accounts)
- Sample journal entries, invoices, and expense categories

### 6. Start the Server

```bash
python3 manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.

---

## LOGIN CREDENTIALS

| Email | Password | Role | Access Level |
|---|---|---|---|
| admin@school.edu | admin123 | Administrator | Full access |
| accountant@school.edu | demo123 | Accountant | Ledger, Receivables, Payables, Reports |
| finance@school.edu | demo123 | Finance Officer | Ledger, Receivables, Payables, Approvals |
| auditor@school.edu | demo123 | Auditor | Reports & Audit Log only |
| teacher@school.edu | demo123 | Teacher | Dashboard only |

---

## PROJECT STRUCTURE

```
school_fms/
├── manage.py                    # Django entry point
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables
├── db.sqlite3                   # SQLite database (auto-created)
├── config/
│   └── settings/
│       ├── base.py              # Shared settings
│       ├── development.py       # Local dev (SQLite, DEBUG=True)
│       └── production.py        # Production (MySQL, DEBUG=False)
├── apps/
│   ├── users/                   # Authentication, roles, audit log
│   ├── general_ledger/          # Chart of Accounts, Journal Entries
│   ├── accounts_receivable/     # Students, Invoices, Payments
│   ├── accounts_payable/        # Vendors, Expenses, Approvals
│   └── reports/                 # Balance Sheet, Income Statement, etc.
├── templates/                   # HTML templates
└── static/                      # CSS, JavaScript
```

---

## TROUBLESHOOTING

| Problem | Solution |
|---|---|
| `command not found: python3` | Use `python` instead of `python3` |
| `No module named 'django'` | Activate venv: `source venv/bin/activate` |
| `Port 8000 already in use` | Use a different port: `python3 manage.py runserver 8080` |
| `OperationalError: no such table` | Run migrations: `python3 manage.py migrate` |
| `Template does not exist` | Make sure you're in the `school_fms/` directory |
| Blank page / no styles | Check you're at `http://127.0.0.1:8000/`, not `https://` |
| `ModuleNotFoundError` for a package | Run `pip install -r requirements.txt` again |

---

## HOW TO ZIP THIS PROJECT FOR SHARING

Before sharing, **exclude** the virtual environment and database to keep the zip small:

```bash
# From the parent directory of school_fms:
zip -r school_fms.zip school_fms/ \
  -x "school_fms/venv/*" \
  -x "school_fms/db.sqlite3" \
  -x "school_fms/__pycache__/*" \
  -x "school_fms/apps/*/__pycache__/*" \
  -x "school_fms/*.pyc"
```

The recipient runs the setup steps above to recreate venv and database.

---

## CURRENCY & LOCALE

This system is configured for **Ghanaian Cedis (GH₵)**. All amounts, reports, and exports display in GHS.
