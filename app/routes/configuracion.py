from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
import sqlite3
from flask_paginate import Pagination, get_page_parameter
import os
from datetime import datetime

bp = Blueprint('configuracion', __name__)

def get_users(offset=0, per_page=10):
    conn = sqlite3.connect('users.db')
    users = conn.execute('SELECT username, role FROM users LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    users_with_folders = []
    for user in users:
        username, role = user
        folders = get_user_folders(role)
        users_with_folders.append(dict(username=username, role=role, folders=folders))
    conn.close()
    return users_with_folders

def get_folders():
    root_folder = 'uploads'
    subfolders = [root_folder]
    for item in os.listdir(root_folder):
        item_path = os.path.join(root_folder, item)
        if os.path.isdir(item_path):
            subfolders.append(item)
    return subfolders

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

def update_user_folders(role, folders):
    conn = sqlite3.connect('users.db')
    conn.execute('UPDATE roles SET folders = ? WHERE role = ?', (folders, role))
    conn.commit()
    conn.close()

def get_user_folders(role):
    conn = sqlite3.connect('users.db')
    folders = conn.execute('SELECT folders FROM roles WHERE role = ?', (role,)).fetchone()
    conn.close()
    return folders[0].split(',') if folders else []

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

def delete_auditoria(start_date, end_date):
    conn = sqlite3.connect('auditoria.db')
    conn.execute('DELETE FROM auditoria WHERE fecha_subida BETWEEN ? AND ?', (start_date, end_date))
    conn.commit()
    conn.close()

def delete_respaldo(start_date, end_date):
    conn = sqlite3.connect('respaldo.db')
    backups = conn.execute('SELECT archivo FROM respaldos WHERE fecha BETWEEN ? AND ?', (start_date, end_date)).fetchall()
    for backup in backups:
        backup_path = os.path.join(current_app.config['BACKUP_FOLDER'], backup[0])
        if os.path.exists(backup_path):
            os.remove(backup_path)
    conn.execute('DELETE FROM respaldos WHERE fecha BETWEEN ? AND ?', (start_date, end_date))
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
            update_user_folders(role, ','.join(folders))
            flash(f'Rol de {username} actualizado a {role} con permisos a {", ".join(folders)}.')
        elif 'frecuencia' in request.form:
            frecuencia = request.form['frecuencia']
            update_backup_frequency(frecuencia)
            flash(f'Frecuencia de respaldo actualizada a {frecuencia} días.')
        elif 'delete_auditoria' in request.form:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            delete_auditoria(start_date, end_date)
            flash(f'Registros de auditoría eliminados del {start_date} al {end_date}.')
        elif 'delete_respaldo' in request.form:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            delete_respaldo(start_date, end_date)
            flash(f'Registros de respaldo eliminados del {start_date} al {end_date}.')
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
