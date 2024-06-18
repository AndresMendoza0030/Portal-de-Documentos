from flask import Blueprint, render_template, redirect, url_for, request, session, flash
import sqlite3

bp = Blueprint('auth', __name__)

def get_user(username):
    conn = sqlite3.connect('users.db')
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and user[2] == password:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user[3]
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash("Credenciales incorrectas")
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
