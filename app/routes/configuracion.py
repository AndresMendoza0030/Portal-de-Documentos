from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import sqlite3
from flask_paginate import Pagination, get_page_parameter

bp = Blueprint('configuracion', __name__)

def get_users(offset=0, per_page=10):
    conn = sqlite3.connect('users.db')
    users = conn.execute('SELECT username, role, folders FROM users LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    conn.close()
    return [dict(username=row[0], role=row[1], folders=row[2]) for row in users]

def get_folders():
    conn = sqlite3.connect('users.db')
    folders = conn.execute('SELECT DISTINCT folders FROM roles').fetchall()
    conn.close()
    return [folder[0] for folder in folders]

def get_roles():
    conn = sqlite3.connect('users.db')
    roles = conn.execute('SELECT role FROM roles').fetchall()
    conn.close()
    return [role[0] for role in roles]

def get_total_users():
    conn = sqlite3.connect('users.db')
    total = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    conn.close()
    return total

def update_user_role(username, role):
    conn = sqlite3.connect('users.db')
    conn.execute('UPDATE users SET role = ? WHERE username = ?', (role, username))
    conn.commit()
    conn.close()

def update_user_folders(username, folders):
    conn = sqlite3.connect('users.db')
    conn.execute('UPDATE users SET folders = ? WHERE username = ?', (folders, username))
    conn.commit()
    conn.close()

def get_backup_frequency():
    conn = sqlite3.connect('respaldo.db')
    frequency = conn.execute('SELECT valor FROM frequency WHERE clave = ?', ('frecuencia_respaldo',)).fetchone()
    conn.close()
    return frequency[0] if frequency else '7'
def update_backup_frequency(new_frequency):
    conn = sqlite3.connect('respaldo.db')
    conn.execute('UPDATE frequency SET valor = ? WHERE clave = ?', (new_frequency, 'frecuencia_respaldo'))
    conn.commit()
    conn.close()

@bp.route('/configuracion', methods=['GET', 'POST'])
def configuracion():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        if 'username' in request.form and 'role' in request.form:
            username = request.form['username']
            role = request.form['role']
            folders = request.form.getlist('folders')
            update_user_role(username, role)
            update_user_folders(username, ','.join(folders))
            flash(f'Rol de {username} actualizado a {role} con permisos a {", ".join(folders)}.')
        elif 'frecuencia' in request.form:
            frecuencia = request.form['frecuencia']
            update_backup_frequency(frecuencia)
            flash(f'Frecuencia de respaldo actualizada a {frecuencia} días.')
        return redirect(url_for('configuracion.configuracion'))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10
    offset = (page - 1) * per_page
    total = get_total_users()
    users = get_users(offset=offset, per_page=per_page)
    roles = get_roles()
    folders = get_folders()
    frecuencia = get_backup_frequency()

    pagination = Pagination(page=page, total=total, per_page=per_page, css_framework='bootstrap4')

    return render_template('configuracion.html', users=users, roles=roles, folders=folders, frecuencia=frecuencia, page=page, per_page=per_page, pagination=pagination)
