from flask import Blueprint, render_template, redirect, url_for, request, session, send_from_directory, flash, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import time
from ..models import get_db_connection, get_backup_db_connection, get_user_role, get_user_folders
import tarfile
import zipfile
import shutil

bp = Blueprint('document', __name__)

ALLOWED_EXTENSIONS = {'pptx', 'docx', 'pdf', 'xlsx'}

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_tree(folder, allowed_folders):
    def recursive_scan(directory):
        tree = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                if any(allowed in item_path for allowed in allowed_folders):
                    tree.append({
                        "text": item,
                        "children": recursive_scan(item_path),
                        "type": "folder",
                        "icon": "static/images/icons/folder.png"
                    })
            else:
                ext = item.split('.').pop().lower()
                iconsPath = 'static/images/icons/'
                icon = iconsPath + 'file.png'
                if ext == 'pdf':
                    icon = iconsPath + 'pdf.png'
                elif ext == 'docx':
                    icon = iconsPath + 'docx.png'
                elif ext == 'pptx':
                    icon = iconsPath + 'pptx.png'
                elif ext == 'xlsx':
                    icon = iconsPath + 'xlsx.png'
                tree.append({
                    "text": item,
                    "a_attr": {"href": url_for('document.view_file', filename=os.path.relpath(item_path, folder).replace('\\', '/'))},
                    "type": "file",
                    "icon": icon
                })
        return tree

    return recursive_scan(folder)

@bp.route('/documents')
def documents():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    role = session.get('role')
    allowed_folders = get_user_folders(role)
    
    file_tree = get_file_tree(current_app.config['UPLOAD_FOLDER'], allowed_folders)
    return render_template('documents.html', files=file_tree)

@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        if 'file' not in request.files or 'selected-folder' not in request.form:
            return redirect(request.url)
        file = request.files['file']
        selected_folder = request.form['selected-folder']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], selected_folder, filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            
            if os.path.exists(upload_path):
                handle_file_replacement(file, filename, upload_path)
                flash(f'Archivo {filename} reemplazado con éxito.')
            else:
                handle_new_file_upload(file, filename, upload_path)
                flash(f'Archivo {filename} subido con éxito.')

            return redirect(url_for('document.documents'))

    folder_tree_data = build_folder_tree(current_app.config['UPLOAD_FOLDER'], session.get('role'))
    return render_template('upload.html', folder_tree_data=folder_tree_data)

def build_folder_tree(root_folder, role):
    allowed_folders = get_user_folders(role)
    tree = []
    for item in os.listdir(root_folder):
        item_path = os.path.join(root_folder, item)
        if os.path.isdir(item_path):
            if any(allowed in item_path for allowed in allowed_folders):
                node = {
                    "text": item,
                    "path": item.replace('\\', '/'),
                    "children": build_folder_tree(item_path, role)
                }
                tree.append(node)
    return tree

def handle_file_replacement(file, filename, upload_path):
    file.save(upload_path)

    previous_entry = None
    for attempt in range(5):
        try:
            conn = get_db_connection()
            previous_entry = conn.execute('SELECT * FROM auditoria WHERE documento = ? ORDER BY id DESC LIMIT 1', (filename,)).fetchone()
            if previous_entry:
                previous_version = float(previous_entry['version'])
                new_version = previous_version + 0.1
                conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor, fecha_edicion, usuario, version) VALUES (?, ?, ?, ?, ?, ?)',
                             (previous_entry['fecha_subida'], filename, previous_entry['autor'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session['username'], f'{new_version:.1f}'))
                
            else:
                conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor, fecha_edicion, usuario, version) VALUES (?, ?, ?, ?, ?, ?)',
                             (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename, session['username'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session['username'], '1.0'))
            conn.commit()
            conn.close()
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(1)
            else:
                raise
    create_backup(is_individual=True, file_path=upload_path)

def handle_file_replacement(file, filename, upload_path):
    file.save(upload_path)
    for attempt in range(5):
        try:
            conn = get_db_connection()
            previous_entry = conn.execute('SELECT * FROM auditoria WHERE documento = ? ORDER BY id DESC LIMIT 1', (filename,)).fetchone()
            
            if previous_entry:
                previous_version = float(previous_entry['version'])
                new_version = previous_version + 0.1
                conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor, fecha_edicion, usuario, version) VALUES (?, ?, ?, ?, ?, ?)',
                             (previous_entry['fecha_subida'], filename, previous_entry['autor'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session['username'], f'{new_version:.1f}'))
            else:
                conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor, fecha_edicion, usuario, version) VALUES (?, ?, ?, ?, ?, ?)',
                             (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename, session['username'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session['username'], '1.0'))
            conn.commit()
            conn.close()
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(1)
            else:
                raise
    create_backup(is_individual=True, file_path=upload_path)

def handle_new_file_upload(file, filename, upload_path):
    file.save(upload_path)
    for attempt in range(5):
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor, version) VALUES (?, ?, ?, ?)',
                         (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename, session['username'], '1.0'))
            conn.commit()
            conn.close()
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(1)
            else:
                raise
@bp.route('/view/<path:filename>', methods=['GET', 'POST'])
def view_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            file.save(full_path)
            flash('Archivo reemplazado con éxito.')
            return redirect(url_for('document.view_file', filename=filename))
        else:
            flash('Error al subir el archivo. Asegúrate de que el archivo sea del tipo permitido.')
    
    # Genera la URL para la descarga del archivo correctamente
    file_url = url_for('document.uploaded_file', filename=filename, _external=True)
    return render_template('view_file.html', filename=filename, file_url=file_url)


@bp.route('/uploads/<path:filename>', methods=['GET'])
def uploaded_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash('El archivo no existe.')
        return redirect(url_for('document.documents'))
    
    # Asegúrate de usar send_from_directory correctamente
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    return send_from_directory(directory, filename)

@bp.route('/get_subfolders', methods=['POST'])
def get_subfolders():
    data = request.get_json()
    folder = data.get('folder')
    folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    subfolders = []
    if os.path.isdir(folder_path):
        subfolders = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
    return {'subfolders': subfolders}
@bp.route('/create_folder', methods=['POST'])
def create_folder():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
   
    folder_name = request.form['folder_name']
    parent_folder = request.form['parent_folder']
    if not parent_folder:
        print('Parent folder is missing.')
        return 'error: parent_folder is required', 400

    parent_folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], parent_folder)
    new_folder_path = os.path.join(parent_folder_path, folder_name)
    try:
        os.makedirs(new_folder_path, exist_ok=True)
        print(f'Folder created successfully: {new_folder_path}')

        # Registro en la tabla de auditoría
        conn.execute('INSERT INTO auditoria (fecha_subida, documento,  autor) VALUES (?,  ?, ?)',
                     (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f'Creó Carpeta {folder_name}',  session['username']))
        conn.commit()
        conn.close()
        return 'success', 200
    except OSError as e:
        print(f'Error creating folder: {str(e)}')
        return f'error: {str(e)}', 400

@bp.route('/delete_folder', methods=['POST'])
def delete_folder():
    conn = get_db_connection()
    
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    folder_path = request.form.get('folder_path')
    if not folder_path:
        print('Folder path is missing.')
        return 'error: missing folder_path', 400

    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_path)
    conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor) VALUES (?, ?, ?)',
                         (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f'Eliminó Carpeta {folder_path}',  session['username']))
    conn.commit()
    conn.close()
    try:
        if os.path.exists(full_path) and os.path.isdir(full_path):
              # Registro en la tabla de auditoría
           
            shutil.rmtree(full_path)
            print(f'Folder deleted successfully: {full_path}')

          
            
            return 'success', 200
        else:
            print(f'Folder does not exist: {full_path}')
            return 'error: folder does not exist', 400
    except Exception as e:
        print(f'Error deleting folder: {str(e)}')
        return f'error: {str(e)}', 400

@bp.route('/delete_file', methods=['POST'])
def delete_file():
    conn = get_db_connection()
    
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    file_path = request.form.get('folder_path')
    # Extrae el nombre del archivo del path
    filename = os.path.basename(file_path)
    
    # Consulta en la base de datos usando el nombre del archivo
    previous_entry = conn.execute('SELECT * FROM auditoria WHERE documento = ? ORDER BY id DESC LIMIT 1', (filename,)).fetchone()
    
    if not file_path:
        print('Folder path is missing.')
        return 'error: missing folder_path', 400
    # Extrae el nombre del archivo del path
  
    
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)

    try:
        if os.path.exists(full_path) and os.path.isfile(full_path): # Registro en la tabla de auditoría
            previous_version = float(previous_entry['version'])
            conn.execute('INSERT INTO auditoria (fecha_subida, documento,  autor, usuario,version) VALUES (?, ?, ?,?,? )',
                         (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f'Eliminó Archivo {file_path}',  session['username'], session['username'],previous_version))
            os.remove(full_path)
            print(f'File deleted successfully: {full_path}')
            conn.commit()
            conn.close()
           
            
            return 'success', 200
        else:
            print(f'File does not exist: {full_path}')
            return 'error: file does not exist', 400
    except Exception as e:
        print(f'Error deleting file: {str(e)}')
        return f'error: {str(e)}', 400

@bp.route('/rename', methods=['POST'])
def rename():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
    old_path = request.form['old_path']
    new_name = request.form['new_name']
    full_old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_path)
    new_path = os.path.join(os.path.dirname(full_old_path), new_name)
    
    try:
        if os.path.exists(full_old_path):
            os.rename(full_old_path, new_path)
            
            conn = get_db_connection()
            conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor) VALUES (?, ?, ?)',
                         (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f'Renombró {old_path} a {new_name}', session['username']))
            conn.commit()
            conn.close()
            
            return 'success', 200
        else:
            print(f'File/folder does not exist: {full_old_path}')
            return 'error: file/folder does not exist', 400
    except Exception as e:
        print(f'Error renaming: {str(e)}')
        return f'error: {str(e)}', 400
