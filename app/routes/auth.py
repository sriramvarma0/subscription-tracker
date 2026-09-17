from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from app.services.user_service import UserService

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        user = UserService.get_user_by_id(user_id)
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        action = request.form.get('action', 'login')
        email = request.form.get('email', '')
        password = request.form.get('password', '')

        if action == 'signup':
            confirm_password = request.form.get('confirm_password', '')
            try:
                user = UserService.register_user(email, password, confirm_password)
                session['user_id'] = user.id
                flash('Account created successfully! Welcome to Subscription Tracker.', 'success')
                return redirect(url_for('dashboard.index'))
            except ValueError as e:
                flash(str(e), 'error')
                return render_template('auth/login.html', active_tab='signup', email=email), 400

        elif action == 'set_password':
            user_id = request.form.get('user_id') or session.get('pending_user_id')
            user = UserService.get_user_by_id(user_id) if user_id else None
            confirm_password = request.form.get('confirm_password', '')
            if not user:
                flash('Session expired. Please enter your email again.', 'error')
                return redirect(url_for('auth.login'))
            try:
                user = UserService.set_user_password(user, password, confirm_password)
                session.pop('pending_user_id', None)
                session['user_id'] = user.id
                flash('Password set successfully! Your account is now secured.', 'success')
                return redirect(url_for('dashboard.index'))
            except ValueError as e:
                flash(str(e), 'error')
                return render_template('auth/login.html', active_tab='set_password', pending_user=user, email=user.email), 400

        else: # login
            try:
                status, user = UserService.authenticate_user(email, password)
                if status == 'NEEDS_PASSWORD_SET':
                    session['pending_user_id'] = user.id
                    flash('Your account currently has no password. Please set a password to upgrade your account security.', 'info')
                    return render_template('auth/login.html', active_tab='set_password', pending_user=user, email=user.email)
                elif status == 'SUCCESS':
                    session['user_id'] = user.id
                    flash('Logged in successfully.', 'success')
                    return redirect(url_for('dashboard.index'))
            except ValueError as e:
                flash(str(e), 'error')
                return render_template('auth/login.html', active_tab='login', email=email), 400

    active_tab = request.args.get('tab', 'login')
    return render_template('auth/login.html', active_tab=active_tab)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        try:
            user = UserService.register_user(email, password, confirm_password)
            session['user_id'] = user.id
            flash('Account created successfully! Welcome to Subscription Tracker.', 'success')
            return redirect(url_for('dashboard.index'))
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('auth/login.html', active_tab='signup', email=email), 400
    return render_template('auth/login.html', active_tab='signup')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
