import sqlite3
from flask import current_app

def get_db_connection():
    conn = sqlite3.connect('auditoria.db', timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def get_backup_db_connection():
    conn = sqlite3.connect('respaldo.db', timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

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
def create_frequency_table():
    conn = sqlite3.connect('respaldo.db')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS frequency (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clave TEXT UNIQUE NOT NULL,
        valor TEXT NOT NULL
    )
    ''')
    conn.execute('''
    INSERT OR IGNORE INTO frequency (clave, valor) VALUES ('frecuencia_respaldo', '7')
    ''')
    conn.commit()
    conn.close()
def create_roles_table():
    conn = sqlite3.connect('users.db')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL UNIQUE,
        folders TEXT
    )
    ''')
    conn.commit()
    conn.close()

create_roles_table()
# Crear tablas si no existen
create_auditoria_table()
create_frequency_table()
create_backup_table()
def get_user_role(username):
    conn = sqlite3.connect('users.db')
    role = conn.execute('SELECT role FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return role[0] if role else None

def get_user_folders(role):
    conn = sqlite3.connect('users.db')
    folders = conn.execute('SELECT folders FROM roles WHERE role = ?', (role,)).fetchone()
    conn.close()
    return folders[0].split(',') if folders and folders[0] else []
