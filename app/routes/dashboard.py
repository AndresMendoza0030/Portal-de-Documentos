from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')
