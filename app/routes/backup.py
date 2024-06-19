import os
import tarfile
import shutil
import zipfile
from flask import Blueprint, render_template, redirect, url_for, request, session, send_from_directory, flash, current_app
from datetime import datetime
from ..models import get_backup_db_connection

bp = Blueprint('backup', __name__)

def create_backup(is_individual=False, file_path=None):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    version_info = timestamp
    if is_individual and file_path:
        backup_name = os.path.basename(file_path)
        backup_path = os.path.join(current_app.config['BACKUP_FOLDER'], backup_name)
        shutil.copy(file_path, backup_path)

        # Obtener la versión del archivo respaldado
        conn = get_db_connection()
        entry = conn.execute('SELECT version FROM auditoria WHERE documento = ? ORDER BY id DESC LIMIT 1', (backup_name,)).fetchone()
        version_info = entry['version'] if entry else '1.0'
        conn.close()
    else:
        backup_name = f'backup_{timestamp}.tar.gz'
        backup_path = os.path.join(current_app.config['BACKUP_FOLDER'], backup_name)
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(current_app.config['UPLOAD_FOLDER'], arcname=os.path.basename(current_app.config['UPLOAD_FOLDER']))

    # Registrar en la base de datos de respaldo
    conn = get_backup_db_connection()
    conn.execute('INSERT INTO respaldos (fecha, archivo, autor, version) VALUES (?, ?, ?, ?)',
                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), backup_name, session['username'], version_info))
    conn.commit()
    conn.close()
    return backup_name

def get_backup_history(page, per_page):
    offset = (page - 1) * per_page
    conn = get_backup_db_connection()
    backups = conn.execute('SELECT * FROM respaldos ORDER BY fecha DESC LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    total = conn.execute('SELECT COUNT(*) FROM respaldos').fetchone()[0]
    conn.close()
    return backups, total

@bp.route('/respaldo/manual', methods=['POST'])
def manual_backup():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    backup_name = create_backup()
    flash(f'Respaldo {backup_name} creado con éxito.')
    return redirect(url_for('backup.respaldo'))

@bp.route('/respaldo/download/<filename>')
def download_backup(filename):
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    backup_folder = current_app.config['BACKUP_FOLDER']
    backup_path = os.path.join(backup_folder, filename)
     # Impresiones para depuración
    print(f"Folder: {backup_folder}")
    print(f"Filename: {filename}")
    print(f"Backup Path: {backup_path}")
    if not os.path.exists(backup_path):
        flash(f'El archivo {filename} no existe en la carpeta de respaldos.')
        return redirect(url_for('backup.respaldo'))

    return send_from_directory(backup_folder, filename, as_attachment=True)

@bp.route('/respaldo/download_all')
def download_all_backups():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    archive_name = f'all_backups_{timestamp}.zip'
    archive_path = os.path.join(current_app.config['TEMP_FOLDER'], archive_name)
    
    with zipfile.ZipFile(archive_path, 'w') as zipf:
        for root, dirs, files in os.walk(current_app.config['BACKUP_FOLDER']):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=os.path.relpath(file_path, current_app.config['BACKUP_FOLDER']))
    
    return send_from_directory(current_app.config['TEMP_FOLDER'], archive_name, as_attachment=True)

@bp.route('/respaldo')
def respaldo():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    backups, total = get_backup_history(page, per_page)
    return render_template('respaldo.html', backups=backups, total=total, page=page, per_page=per_page)
