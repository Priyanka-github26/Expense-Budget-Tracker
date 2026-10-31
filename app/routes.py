
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from calendar import month_name
from datetime import date
from decimal import Decimal, InvalidOperation
from sqlalchemy import func

from app import app, db, bcrypt, login_manager
from app.models import User, Expense, Category, Budget, Income, SavingsGoal
import csv
from io import StringIO
from flask import make_response

# Load logged-in user
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Home
@app.route('/')
def home():
    return redirect(url_for('login'))


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required.')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Password must contain at least 8 characters.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))

        try:
            hashed_password = bcrypt.generate_password_hash(
                password
            ).decode('utf-8')

            new_user = User(
                username=username,
                email=email,
                password=hashed_password
            )

            db.session.add(new_user)
            db.session.flush()

            default_categories = [
                'Food',
                'Travel',
                'Shopping',
                'Bills',
                'Education',
                'Health',
                'Entertainment',
                'Other'
            ]

            for category_name in default_categories:
                category = Category(
                    name=category_name,
                    user_id=new_user.id
                )
                db.session.add(category)

            db.session.commit()

            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))

        except Exception as error:
            db.session.rollback()
            print('Registration error:', error)
            flash('Registration failed. Please try again.')

    return render_template('register.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.')

    return render_template('login.html')


# Logout
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()

    month_start = today.replace(day=1)

    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)

    monthly_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= month_start,
        Expense.date < next_month
    ).all()

    monthly_income = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= month_start,
        Income.date < next_month
    ).all()

    total_expenses = sum(
        (expense.amount for expense in monthly_expenses),
        Decimal('0.00')
    )

    total_income = sum(
        (income.amount for income in monthly_income),
        Decimal('0.00')
    )

    monthly_budget = Budget.query.filter_by(
        user_id=current_user.id,
        month=today.month,
        year=today.year,
        category_id=None
    ).first()

    budget_amount = (
        monthly_budget.amount if monthly_budget
        else Decimal('0.00')
    )

    remaining_budget = budget_amount - total_expenses

    return render_template(
        'dashboard.html',
        username=current_user.username,
        total_income=total_income,
        total_expenses=total_expenses,
        budget_amount=budget_amount,
        remaining_budget=remaining_budget
    )

# View expenses
@app.route('/expenses')
@login_required
def expenses():
    user_expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(Expense.date.desc()).all()

    categories = Category.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        'expenses.html',
        expenses=user_expenses,
        categories=categories
    )


# Add expense
@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    title = request.form.get('title', '').strip()
    amount_text = request.form.get('amount', '').strip()
    expense_date = request.form.get('date', '')
    category_id = request.form.get('category_id', '')

    try:
        if not title or not amount_text or not expense_date or not category_id:
            raise ValueError()

        amount = Decimal(amount_text)

        if not amount.is_finite() or amount <= 0:
            raise ValueError()

        selected_date = date.fromisoformat(expense_date)

        category = db.session.get(Category, int(category_id))

        if not category or category.user_id != current_user.id:
            raise ValueError()

        new_expense = Expense(
            title=title,
            amount=amount,
            date=selected_date,
            user_id=current_user.id,
            category_id=category.id
        )

        db.session.add(new_expense)
        db.session.commit()

        flash('Expense added successfully!')

    except (ValueError, TypeError, InvalidOperation):
        db.session.rollback()
        flash('Please enter valid expense details.')

    return redirect(url_for('expenses'))


# Edit expense
@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user.id
    ).first_or_404()

    categories = Category.query.filter_by(
        user_id=current_user.id
    ).all()

    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            amount_text = request.form.get('amount', '').strip()
            expense_date = request.form.get('date', '')
            category_id = request.form.get('category_id', '')

            if not title or not amount_text or not expense_date or not category_id:
                raise ValueError()

            amount = Decimal(amount_text)

            if not amount.is_finite() or amount <= 0:
                raise ValueError()

            selected_date = date.fromisoformat(expense_date)

            category = db.session.get(Category, int(category_id))

            if not category or category.user_id != current_user.id:
                raise ValueError()

            expense.title = title
            expense.amount = amount
            expense.date = selected_date
            expense.category_id = category.id

            db.session.commit()

            flash('Expense updated successfully!')
            return redirect(url_for('expenses'))

        except (ValueError, TypeError, InvalidOperation):
            db.session.rollback()
            flash('Please enter valid expense details.')

    return render_template(
        'edit_expense.html',
        expense=expense,
        categories=categories
    )


# Delete expense
@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(expense)
    db.session.commit()

    flash('Expense deleted successfully!')

    return redirect(url_for('expenses'))


# Monthly budget management
@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():

    month_names = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }

    if request.method == 'POST':
        try:
            amount_text = request.form.get('amount', '').strip()
            month = int(request.form.get('month', ''))
            year = int(request.form.get('year', ''))

            amount = Decimal(amount_text)

            if (
                not amount.is_finite()
                or amount <= 0
                or month < 1
                or month > 12
                or year < 2000
                or year > 2100
            ):
                raise ValueError()

            existing_budget = Budget.query.filter_by(
                user_id=current_user.id,
                month=month,
                year=year,
                category_id=None
            ).first()

            if existing_budget:
                existing_budget.amount = amount
                flash('Monthly budget updated successfully!')

            else:
                new_budget = Budget(
                    amount=amount,
                    month=month,
                    year=year,
                    user_id=current_user.id,
                    category_id=None
                )

                db.session.add(new_budget)
                flash('Monthly budget saved successfully!')

            db.session.commit()

        except (ValueError, TypeError, InvalidOperation):
            db.session.rollback()
            flash('Please enter valid budget details.')

    user_budgets = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=None
    ).order_by(
        Budget.year.desc(),
        Budget.month.desc()
    ).all()

    return render_template(
        'budgets.html',
        budgets=user_budgets,
        month_names=month_names
    )

# View income
@app.route('/income')
@login_required
def income():
    user_income = Income.query.filter_by(
        user_id=current_user.id
    ).order_by(Income.date.desc()).all()

    return render_template(
        'income.html',
        incomes=user_income
    )


# Add income
@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    source = request.form.get('source', '').strip()
    amount_text = request.form.get('amount', '').strip()
    income_date = request.form.get('date', '')

    try:
        if not source or not amount_text or not income_date:
            raise ValueError()

        amount = Decimal(amount_text)

        if not amount.is_finite() or amount <= 0:
            raise ValueError()

        selected_date = date.fromisoformat(income_date)

        new_income = Income(
            source=source,
            amount=amount,
            date=selected_date,
            user_id=current_user.id
        )

        db.session.add(new_income)
        db.session.commit()

        flash('Income added successfully!')

    except (ValueError, TypeError, InvalidOperation):
        db.session.rollback()
        flash('Please enter valid income details.')

    return redirect(url_for('income'))


# Savings Goals Management

@app.route('/savings', methods=['GET', 'POST'])
@login_required
def savings():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        target_text = request.form.get('target_amount', '').strip()
        current_text = request.form.get('current_amount', '0').strip()
        deadline_text = request.form.get('deadline', '').strip()

        try:
            if not title or not target_text:
                raise ValueError()

            target_amount = Decimal(target_text)
            current_amount = Decimal(current_text)

            if (not target_amount.is_finite() or
                not current_amount.is_finite() or
                target_amount <= 0 or current_amount < 0 or
                current_amount > target_amount):
                raise ValueError()

            deadline = (
                date.fromisoformat(deadline_text)
                if deadline_text else None
            )

            new_goal = SavingsGoal(
                title=title,
                target_amount=target_amount,
                current_amount=current_amount,
                deadline=deadline,
                user_id=current_user.id
            )

            db.session.add(new_goal)
            db.session.commit()
            flash('Savings goal created successfully!')

        except (ValueError, TypeError, InvalidOperation):
            db.session.rollback()
            flash('Please enter valid savings goal details.')

        return redirect(url_for('savings'))

    user_goals = SavingsGoal.query.filter_by(
        user_id=current_user.id
    ).order_by(SavingsGoal.id.desc()).all()

    return render_template('savings.html', goals=user_goals)


# Update savings progress
@app.route('/update_savings/<int:goal_id>', methods=['POST'])
@login_required
def update_savings(goal_id):
    goal = SavingsGoal.query.filter_by(
        id=goal_id,
        user_id=current_user.id
    ).first_or_404()

    try:
        current_text = request.form.get('current_amount', '').strip()
        current_amount = Decimal(current_text)

        if (not current_amount.is_finite() or
            current_amount < 0 or
            current_amount > goal.target_amount):
            raise ValueError()

        goal.current_amount = current_amount
        db.session.commit()
        flash('Savings progress updated successfully!')

    except (ValueError, TypeError, InvalidOperation):
        db.session.rollback()
        flash('Please enter a valid savings amount.')

    return redirect(url_for('savings'))


# Delete savings goal
@app.route('/delete_savings/<int:goal_id>', methods=['POST'])
@login_required
def delete_savings(goal_id):
    goal = SavingsGoal.query.filter_by(
        id=goal_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(goal)
    db.session.commit()

    flash('Savings goal deleted successfully!')
    return redirect(url_for('savings'))


# Analytics Dashboard
@app.route('/analytics')
@login_required
def analytics():

    today = date.today()
    month_start = today.replace(day=1)

    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)

    # Category-wise expenses for current month
    category_data = db.session.query(
        Category.name,
        func.sum(Expense.amount)
    ).join(
        Expense, Expense.category_id == Category.id
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= month_start,
        Expense.date < next_month
    ).group_by(Category.name).all()

    category_labels = [item[0] for item in category_data]
    category_amounts = [float(item[1]) for item in category_data]

    # Monthly income and expenses for the last 6 months
    month_labels = []
    monthly_expenses = []
    monthly_income = []

    for i in range(5, -1, -1):

        month_index = today.year * 12 + today.month - 1 - i
        year = month_index // 12
        month = month_index % 12 + 1

        start_date = date(year, month, 1)

        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        expense_total = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date < end_date
        ).scalar() or Decimal('0.00')

        income_total = db.session.query(
            func.sum(Income.amount)
        ).filter(
            Income.user_id == current_user.id,
            Income.date >= start_date,
            Income.date < end_date
        ).scalar() or Decimal('0.00')

        month_labels.append(start_date.strftime('%b %Y'))
        monthly_expenses.append(float(expense_total))
        monthly_income.append(float(income_total))

    # Current month's overall budget
    monthly_budget = Budget.query.filter_by(
        user_id=current_user.id,
        month=today.month,
        year=today.year,
        category_id=None
    ).first()

    budget_amount = float(
        monthly_budget.amount if monthly_budget
        else Decimal('0.00')
    )

    current_month_expenses = sum(
        monthly_expenses[-1:]
    )

    return render_template(
        'analytics.html',
        category_labels=category_labels,
        category_amounts=category_amounts,
        month_labels=month_labels,
        monthly_expenses=monthly_expenses,
        monthly_income=monthly_income,
        budget_amount=budget_amount,
        current_month_expenses=current_month_expenses
    )



@app.route('/reports')
@login_required
def reports():

    today = date.today()

    # Get selected month and year
    try:
        selected_month = int(request.args.get('month', today.month))
        selected_year = int(request.args.get('year', today.year))

        if selected_month not in range(1, 13):
            raise ValueError()

        if selected_year < 2000 or selected_year > today.year + 1:
            raise ValueError()

    except (ValueError, TypeError):
        selected_month = today.month
        selected_year = today.year

    # Calculate date range
    start_date = date(selected_year, selected_month, 1)

    if selected_month == 12:
        end_date = date(selected_year + 1, 1, 1)
    else:
        end_date = date(selected_year, selected_month + 1, 1)

    # Calculate total income
    total_income = db.session.query(
        func.sum(Income.amount)
    ).filter(
        Income.user_id == current_user.id,
        Income.date >= start_date,
        Income.date < end_date
    ).scalar() or Decimal('0.00')

    # Calculate total expenses
    total_expenses = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date < end_date
    ).scalar() or Decimal('0.00')

    # Calculate net savings
    net_savings = total_income - total_expenses

    # Category-wise expense report
    category_report = db.session.query(
        Category.name,
        func.sum(Expense.amount)
    ).join(
        Expense, Expense.category_id == Category.id
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date < end_date
    ).group_by(Category.name).all()

    # Available years
    first_year = 2024
    years = list(range(first_year, today.year + 1))

    if selected_year not in years:
        years.append(selected_year)
        years.sort()


    # Yearly Financial Summary

    year_start = date(selected_year, 1, 1)
    year_end = date(selected_year + 1, 1, 1)

    # Total yearly income
    yearly_income = db.session.query(
        func.sum(Income.amount)
    ).filter(
        Income.user_id == current_user.id,
        Income.date >= year_start,
        Income.date < year_end
    ).scalar() or Decimal('0.00')

    # Total yearly expenses
    yearly_expenses = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= year_start,
        Expense.date < year_end
    ).scalar() or Decimal('0.00')

    # Yearly net savings
    yearly_savings = yearly_income - yearly_expenses

    # Month-wise breakdown
    yearly_months = []
    yearly_monthly_income = []
    yearly_monthly_expenses = []

    for month in range(1, 13):

        month_start = date(selected_year, month, 1)

        if month == 12:
            month_end = date(selected_year + 1, 1, 1)
        else:
            month_end = date(selected_year, month + 1, 1)

        income = db.session.query(
            func.sum(Income.amount)
        ).filter(
            Income.user_id == current_user.id,
            Income.date >= month_start,
            Income.date < month_end
        ).scalar() or Decimal('0.00')

        expenses = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date < month_end
        ).scalar() or Decimal('0.00')

        yearly_months.append(month_name[month])
        yearly_monthly_income.append(float(income))
        yearly_monthly_expenses.append(float(expenses))



    return render_template(
        'reports.html',
        selected_month=selected_month,
        selected_year=selected_year,
        month_names=[month_name[i] for i in range(1, 13)],
        years=years,

        # Monthly report
        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=net_savings,

        category_report=[
            (category, float(amount))
            for category, amount in category_report
        ],

        # Yearly report
        yearly_income=yearly_income,
        yearly_expenses=yearly_expenses,
        yearly_savings=yearly_savings,
        yearly_months=yearly_months,
        yearly_monthly_income=yearly_monthly_income,
        yearly_monthly_expenses=yearly_monthly_expenses
    )


@app.route('/export_report')
@login_required
def export_report():

    today = date.today()

    try:
        selected_month = int(request.args.get('month', today.month))
        selected_year = int(request.args.get('year', today.year))

        if selected_month not in range(1, 13):
            raise ValueError()

        if selected_year < 2000 or selected_year > today.year + 1:
            raise ValueError()

    except (ValueError, TypeError):
        selected_month = today.month
        selected_year = today.year

    start_date = date(selected_year, selected_month, 1)

    if selected_month == 12:
        end_date = date(selected_year + 1, 1, 1)
    else:
        end_date = date(selected_year, selected_month + 1, 1)

    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date < end_date
    ).order_by(Expense.date.asc()).all()

    income_records = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= start_date,
        Income.date < end_date
    ).order_by(Income.date.asc()).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Expense & Budget Tracker - Monthly Report'])
    writer.writerow(['Month', selected_month, 'Year', selected_year])
    writer.writerow([])
    writer.writerow(['Type', 'Title / Source', 'Category', 'Amount', 'Date'])

    for expense in expenses:
        writer.writerow([
            'Expense',
            expense.title,
            expense.category.name,
            expense.amount,
            expense.date
        ])

    for income in income_records:
        writer.writerow([
            'Income',
            income.source,
            '-',
            income.amount,
            income.date
        ])

    response = make_response('\ufeff' + output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = (
        f'attachment; filename=financial_report_{selected_year}_{selected_month}.csv'
    )

    return response


# Edit Income
@app.route('/edit_income/<int:income_id>', methods=['GET', 'POST'])
@login_required
def edit_income(income_id):

    income = Income.query.filter_by(
        id=income_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == 'POST':
        try:
            source = request.form.get('source', '').strip()
            amount_text = request.form.get('amount', '').strip()
            income_date = request.form.get('date', '').strip()

            if not source or not amount_text or not income_date:
                raise ValueError()

            amount = Decimal(amount_text)

            if not amount.is_finite() or amount <= 0:
                raise ValueError()

            selected_date = date.fromisoformat(income_date)

            income.source = source
            income.amount = amount
            income.date = selected_date

            db.session.commit()
            flash('Income updated successfully!')
            return redirect(url_for('income'))

        except (ValueError, TypeError, InvalidOperation):
            db.session.rollback()
            flash('Please enter valid income details.')

    return render_template('edit_income.html', income=income)


# Delete Income
@app.route('/delete_income/<int:income_id>', methods=['POST'])
@login_required
def delete_income(income_id):

    income = Income.query.filter_by(
        id=income_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(income)
    db.session.commit()

    flash('Income deleted successfully!')
    return redirect(url_for('income'))


# Export Income as CSV
@app.route('/export_income')
@login_required
def export_income():
    incomes = Income.query.filter_by(
        user_id=current_user.id
    ).order_by(Income.date.desc()).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Income Source', 'Amount (INR)', 'Date'])

    for income in incomes:
        writer.writerow([
            income.source,
            income.amount,
            income.date.strftime('%d-%m-%Y')
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=income_report.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response
