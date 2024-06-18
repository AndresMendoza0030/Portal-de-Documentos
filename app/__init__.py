from flask import Flask, current_app, session
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sqlite3
import atexit
import os
import tarfile
import shutil
from .models import get_backup_db_connection, get_db_connection

def get_backup_frequency():
    print("Obteniendo la frecuencia de respaldo...")
    conn = sqlite3.connect('respaldo.db')
    frequency = conn.execute('SELECT valor FROM frequency WHERE clave = ?', ('frecuencia_respaldo',)).fetchone()
    conn.close()
    print(f"Frecuencia de respaldo obtenida: {frequency[0] if frequency else '7'} días")
    return int(frequency[0]) if frequency else 7  # Valor predeterminado de 7 días

def create_backup(is_individual=False, file_path=None):
    print("Iniciando proceso de respaldo...")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    version_info = timestamp
    if is_individual and file_path:
        backup_name = os.path.basename(file_path)
        backup_path = os.path.join(current_app.config['BACKUP_FOLDER'], backup_name)
        shutil.copy(file_path, backup_path)
        print(f"Archivo individual respaldado: {backup_name}")

        # Obtener la versión del archivo respaldado
        conn = get_db_connection()
        entry = conn.execute('SELECT version FROM auditoria WHERE documento = ? ORDER BY id DESC LIMIT 1', (backup_name,)).fetchone()
        version_info = entry['version'] if entry else '1.0'
        conn.close()
        print(f"Versión del archivo respaldado: {version_info}")
    else:
        backup_name = f'backup_{timestamp}.tar.gz'
        backup_path = os.path.join(current_app.config['BACKUP_FOLDER'], backup_name)
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(current_app.config['UPLOAD_FOLDER'], arcname=os.path.basename(current_app.config['UPLOAD_FOLDER']))
        print(f"Respaldo completo creado: {backup_name}")

    # Registrar en la base de datos de respaldo
    conn = get_backup_db_connection()
    conn.execute('INSERT INTO respaldos (fecha, archivo, autor, version) VALUES (?, ?, ?, ?)',
                 (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), backup_name, 'admin', version_info))
    conn.commit()
    conn.close()
    print(f"Backup {backup_name} registrado en la base de datos en {datetime.now()}")
    return backup_name

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    frequency = get_backup_frequency()

    def backup_job():
        print("Ejecutando tarea programada de respaldo...")
        with app.app_context():
            create_backup()

    # Programa el respaldo para ejecutarse cada "frequency" días
    print(f"Programando tarea de respaldo para cada {frequency} días")
    scheduler.add_job(backup_job, 'interval', days=frequency)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    print("Programador de tareas iniciado.")
    return scheduler

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    print("Inicializando la aplicación Flask...")
    
    # Inicializar el programador dentro del contexto de la aplicación
    with app.app_context():
        global scheduler
        scheduler = start_scheduler(app)
        create_backup()

    # Importar y registrar los blueprints
    from .routes import auth, backup, main, document, audit, dashboard, ayuda, configuracion
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(backup.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(document.bp)
    app.register_blueprint(audit.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(ayuda.bp)
    app.register_blueprint(configuracion.bp)
    
    print("Aplicación Flask inicializada y blueprints registrados.")
    return app

if __name__ == '__main__':
    app = create_app()
    print("Ejecutando la aplicación Flask en modo debug...")
    app.run(debug=True)

