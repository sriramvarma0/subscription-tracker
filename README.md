# Subscription Tracker V1

A lightweight, multi-user personal Subscription Tracker web application built with Python, Flask, SQLAlchemy, SQLite, Jinja2, Lucide icons, and modern Vanilla CSS/JS.

---

## 🌟 Features

- **Email-Based Multi-User Identification**: Simple email entry login flow with strict session-based multi-user data isolation.
- **Dynamic Subscription Status**: Real-time status calculation based on current date:
  - **Active**: Expiry date is > 30 days away.
  - **Expiring Soon**: Expiry date is today or within 30 days.
  - **Expired**: Expiry date has passed.
  - **No Expiry**: Undated recurring subscription.
- **Rich Dashboard Layout**: Stat cards summary, search, status filter pills, sorting options, and glassmorphic subscription cards.
- **Full Subscription Management**: Add, edit, and delete subscriptions with interactive modal dialogs.
- **Dynamic Sponsorship Toggle**: Show/hide sponsor company and account fields based on sponsorship choice.
- **Data Export & Backup**: Download your subscription data as CSV or JSON backup.
- **JSON Import**: Restore subscriptions from a JSON backup file with server-side validation.
- **Automated Test Suite**: 100% passing Pytest test coverage verifying user auth, CRUD, status logic, data isolation, and export/import.

---

## 📋 Requirements

- **Python**: 3.9+
- **Database**: SQLite (default, embedded)

---

## 🚀 Getting Started

### 1. Clone & Navigate to Project Directory

```bash
cd subscription-tracker
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

Copy `.env.example` to create `.env`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

Example environment settings in `.env`:
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-this-in-production
DATABASE_URL=sqlite:///instance/subscription_tracker.db
```

### 5. Database Setup & Migrations

Initialize and upgrade SQLite database schema:

```bash
flask db upgrade
```

---

## 🏃 Running the Application

### Development Server

Run locally with Flask development server:

```bash
python run.py
```
Open your browser at `http://127.0.0.1:5000`.

### Production Server (Gunicorn)

On Linux / macOS:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

On Windows (using Waitress or Gunicorn under WSL/Linux):
```powershell
gunicorn -w 4 -b 127.0.0.1:5000 "run:app"
```

---

## 🧪 Running Automated Tests

Run the Pytest suite:

```bash
pytest
```

---

## 📁 Project Structure

```
subscription-tracker/
├── app/
│   ├── __init__.py            # Flask app factory & extensions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # User ORM model
│   │   └── subscription.py    # Subscription ORM model & status property
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Email identification & session routes
│   │   ├── dashboard.py       # Main dashboard route
│   │   ├── subscriptions.py   # Subscription CRUD routes
│   │   └── export_import.py   # CSV export, JSON backup & import
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py    # User business logic
│   │   └── subscription_service.py # Subscription business logic
│   ├── templates/
│   │   ├── base.html          # Base layout template
│   │   ├── auth/
│   │   │   └── login.html     # Email login form
│   │   └── dashboard/
│   │       └── index.html     # Dashboard layout & modals
│   └── static/
│       ├── css/
│       │   └── style.css      # Dark glassmorphism styling
│       └── js/
│           └── main.js        # Modals, sponsor toggles, search/sort JS
├── migrations/                # Database migrations (Alembic)
├── tests/                     # Automated Pytest suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_subscriptions.py
│   ├── test_isolation.py
│   └── test_export_import.py
├── config.py                  # App configuration settings
├── run.py                     # Entry point runner
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
└── README.md                  # Documentation
```

---

## 🔐 Multi-User Security & Isolation

Each user is identified by their email address. All database queries, edits, deletions, and exports are strictly scoped to `session['user_id']` on the server. Arbitrary `user_id` inputs from clients or browser requests are completely ignored to ensure complete data privacy and isolation between users.
