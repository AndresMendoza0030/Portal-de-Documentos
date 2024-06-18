import os
import sqlite3
import time
from flask import Flask, render_template, redirect, url_for, request, session, send_from_directory, flash, Response
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import tarfile
import zipfile
import shutil
from config import Config
from dotenv import load_dotenv
# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['BACKUP_FOLDER'] = 'backups/'
app.config['TEMP_FOLDER'] = 'temp/'  # Añadir una carpeta temporal
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Crear directorios si no existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
# Definir extensiones permitidas
ALLOWED_EXTENSIONS = {'pptx', 'docx', 'pdf', 'xlsx'}

# Conectar a la base de datos de auditoría
def get_db_connection():
    conn = sqlite3.connect('auditoria.db', timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn
def get_backup_db_connection():
    conn = sqlite3.connect('respaldo.db', timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_name = f'backup_{timestamp}.tar.gz'
    backup_path = os.path.join(app.config['BACKUP_FOLDER'], backup_name)
    
    with tarfile.open(backup_path, "w:gz") as tar:
        tar.add(app.config['UPLOAD_FOLDER'], arcname=os.path.basename(app.config['UPLOAD_FOLDER']))
    
    # Registrar en la base de datos de respaldo
    conn = get_backup_db_connection()
    conn.execute('INSERT INTO respaldos (fecha, archivo, autor) VALUES (?, ?, ?)',
                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), backup_name, session['username']))
    conn.commit()
    conn.close()
    return backup_name

def get_backup_history():
    conn = get_backup_db_connection()
    backups = conn.execute('SELECT * FROM respaldos ORDER BY fecha DESC').fetchall()
    conn.close()
    return backups

def create_backup_table():
    conn = get_backup_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS respaldos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT NOT NULL,
                        archivo TEXT NOT NULL,
                        autor TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

create_backup_table()

# Crear la tabla de auditoría si no existe
def create_auditoria_table():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS auditoria (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha_subida TEXT NOT NULL,
                        documento TEXT NOT NULL,
                        autor TEXT NOT NULL,
                        fecha_edicion TEXT,
                        usuario TEXT
                    )''')
    conn.commit()
    conn.close()

create_auditoria_table()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('dashboard.html', files=files)

@app.route('/respaldo/download/<filename>')
def download_backup(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    return send_from_directory(app.config['BACKUP_FOLDER'], filename, as_attachment=True)

@app.route('/respaldo/download_all')
def download_all_backups():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    archive_name = f'all_backups_{timestamp}.zip'
    archive_path = os.path.join(app.config['TEMP_FOLDER'], archive_name)
    
    with zipfile.ZipFile(archive_path, 'w') as zipf:
        for root, dirs, files in os.walk(app.config['BACKUP_FOLDER']):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=os.path.relpath(file_path, app.config['BACKUP_FOLDER']))
    
    return send_from_directory(app.config['TEMP_FOLDER'], archive_name, as_attachment=True)

@app.route('/respaldo/manual', methods=['POST'])
def manual_backup():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    backup_name = create_backup()
    flash(f'Respaldo {backup_name} creado con éxito.')
    return redirect(url_for('respaldo'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username  # Guarda el nombre de usuario en la sesión
            return redirect(url_for('index'))
        else:
            flash("Credenciales incorrectas")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/documents')
def documents():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    file_tree = get_file_tree(app.config['UPLOAD_FOLDER'])
    return render_template('documents.html', files=file_tree)

@app.route('/logout')
def logout():
    session['logged_in'] = False
    session.pop('username', None)  # Elimina el nombre de usuario de la sesión
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files or 'selected-folder' not in request.form:
            return redirect(request.url)
        file = request.files['file']
        selected_folder = request.form['selected-folder']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_folder, filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            file.save(upload_path)

            # Registrar en la auditoría con retry mechanism
            for attempt in range(5):
                try:
                    conn = get_db_connection()
                    conn.execute('INSERT INTO auditoria (fecha_subida, documento, autor) VALUES (?, ?, ?)',
                                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename, session['username']))
                    conn.commit()
                    conn.close()
                    break
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        time.sleep(1)
                    else:
                        raise

            return redirect(url_for('documents'))

    folder_tree_data = build_folder_tree(app.config['UPLOAD_FOLDER'])
    return render_template('upload.html', folder_tree_data=folder_tree_data)

def build_folder_tree(root_folder, root_path=''):
    tree = []
    for item in os.listdir(root_folder):
        item_path = os.path.join(root_folder, item)
        relative_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            node = {
                "text": item,
                "path": relative_path.replace('\\', '/'),
                "children": build_folder_tree(item_path, relative_path)
            }
            tree.append(node)
    return tree


@app.route('/upload/replace', methods=['POST'])
def replace_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    subfolder = request.form.get('subfolder')
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
        if os.path.exists(upload_path):
            file.save(upload_path)

            # Registrar la edición en la auditoría con retry mechanism
            for attempt in range(5):
                try:
                    conn = get_db_connection()
                    conn.execute('UPDATE auditoria SET fecha_edicion = ?, usuario = ? WHERE documento = ? AND autor = ?',
                                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session['username'], filename, session['username']))
                    conn.commit()
                    conn.close()
                    break
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        time.sleep(1)
                    else:
                        raise

            return redirect(url_for('documents'))
        else:
            flash('El archivo no existe para ser reemplazado')
            return redirect(url_for('documents'))

@app.route('/view/<path:filename>')
def view_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    file_url = url_for('uploaded_file', filename=filename, _external=True)
    return render_template('view_file.html', filename=filename, file_url=file_url)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/auditoria')
def auditoria():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    registros = conn.execute('SELECT * FROM auditoria').fetchall()
    conn.close()
    return render_template('auditoria.html', registros=registros)

@app.route('/auditoria/export/pdf')
def export_auditoria_pdf():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    registros = conn.execute('SELECT * FROM auditoria').fetchall()
    conn.close()

    # Generar el PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Historial de Auditoría", ln=True, align='C')

    pdf.set_font("Arial", size=10)
    for registro in registros:
        pdf.cell(200, 10, txt=f"Fecha de Subida: {registro['fecha_subida']} - Documento: {registro['documento']} - Autor: {registro['autor']} - Fecha de Edición: {registro['fecha_edicion']} - Usuario: {registro['usuario']}", ln=True)

    response = Response(pdf.output(dest='S').encode('latin1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment; filename=auditoria.pdf'
    return response

@app.route('/auditoria/export/excel')
def export_auditoria_excel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    registros = conn.execute('SELECT * FROM auditoria').fetchall()
    conn.close()

    # Convertir a DataFrame de Pandas
    df = pd.DataFrame(registros, columns=['id', 'fecha_subida', 'documento', 'autor', 'fecha_edicion', 'usuario'])
    
    # Generar archivo Excel
    output = os.path.join(app.config['TEMP_FOLDER'], 'auditoria.xlsx')
    df.to_excel(output, index=False, sheet_name='Auditoria')

    return send_from_directory(app.config['TEMP_FOLDER'], 'auditoria.xlsx', as_attachment=True)
def get_file_tree(folder):
    def recursive_scan(directory):
        tree = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                tree.append({
                    "text": item,
                    "children": recursive_scan(item_path),
                    "type": "folder",
                    "icon": "static/images/icons/folder.png"  # Asignar ícono para carpetas
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
                    "a_attr": {"href": url_for('view_file', filename=os.path.relpath(item_path, folder))},
                    "type": "file",
                    "icon": icon  # Asignar ícono para archivos
                })
        return tree

    return recursive_scan(folder)
@app.route('/get_subfolders', methods=['POST'])
def get_subfolders():
    data = request.get_json()
    folder = data.get('folder')
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    subfolders = []
    if os.path.isdir(folder_path):
        subfolders = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
    return {'subfolders': subfolders}



@app.route('/ayuda')
def ayuda():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('ayuda.html')
@app.route('/respaldo')
def respaldo():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    backups = get_backup_history()
    return render_template('respaldo.html', backups=backups)

@app.route('/configuracion')
def configuracion():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('configuracion.html')
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
