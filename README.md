
# Expense & Budget Tracker

A web-based Expense and Budget Tracker developed using Python Flask and MySQL. The application helps users manage their income, track daily expenses, set monthly budgets, monitor savings goals, and view financial reports.

## Features

- User Registration and Login
- Secure Password Hashing
- CSRF Protection
- Dashboard with Financial Summary
- Add, Edit and Delete Expenses
- Monthly Budget Management
- Income Management
- Savings Goals and Progress Tracking
- Expense Analytics with Charts
- Monthly and Yearly Reports
- CSV Export for Financial Records

## Technology Stack

**Frontend**
- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js

**Backend**
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- Flask-WTF

**Database**
- MySQL (XAMPP / MariaDB)

## Project Structure

```text
Expenses & Budget Tracker/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── templates/
│       ├── register.html
│       ├── login.html
│       ├── dashboard.html
│       ├── expenses.html
│       ├── edit_expense.html
│       ├── budgets.html
│       ├── income.html
│       ├── edit_income.html
│       ├── savings.html
│       ├── analytics.html
│       ├── reports.html
│       └── base.html
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd "Expenses & budget tracker"
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Database Setup

1. Install and open XAMPP.
2. Start Apache and MySQL.
3. Open phpMyAdmin.
4. Create a database named:

```sql
CREATE DATABASE expense_tracker;
```

### 6. Configure Secret Key

In PowerShell:

```powershell
$env:SECRET_KEY = "your-long-random-secret-key"
```

### 7. Run the Application

```bash
python -c "from app import app; app.run(debug=True)"
```

Open your browser:

http://127.0.0.1:5000

## Security

- Password hashing using Flask-Bcrypt.
- CSRF protection using Flask-WTF.
- Login-required access to protected features.
- User-specific financial records.

## Future Enhancements

- Responsive dashboard improvements.
- Advanced financial insights.
- Budget alerts and notifications.
- Cloud deployment.

## Author

Developed as a Python Full Stack Development Internship Project.
