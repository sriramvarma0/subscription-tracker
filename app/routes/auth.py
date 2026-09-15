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
    if request.method == 'POST':
        email = request.form.get('email', '')
        try:
            user = UserService.get_or_create_user(email)
            session['user_id'] = user.id
            return redirect(url_for('dashboard.index'))
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('auth/login.html', email=email), 400

    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
