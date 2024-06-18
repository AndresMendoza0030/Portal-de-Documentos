from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('ayuda', __name__)

@bp.route('/ayuda')
def ayuda():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    return render_template('ayuda.html')
