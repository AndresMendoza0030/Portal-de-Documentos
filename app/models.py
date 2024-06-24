import sqlite3
from flask import current_app
from datetime import datetime
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
def get_usersdb_connection():
    conn = sqlite3.connect('users.db', timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def get_recent_activities(username):
    conn = get_usersdb_connection()
    activities = conn.execute('SELECT * FROM activities WHERE user = ? ORDER BY date DESC LIMIT 5', 
                              (username,)).fetchall()
    conn.close()
    return activities

def get_recent_documents(username):
    conn = get_usersdb_connection()
    documents = conn.execute('''
        SELECT DISTINCT filename 
        FROM (
            SELECT * 
            FROM documents 
            WHERE user = ? 
            ORDER BY id DESC
        ) 
        ORDER BY id DESC 
        LIMIT 5
    ''', (username,)).fetchall()
    conn.close()
    return documents


def get_notifications(username):
    conn = get_usersdb_connection()
    notifications = conn.execute('SELECT * FROM notifications WHERE user = ? ORDER BY date DESC LIMIT 5', 
                                 (username,)).fetchall()
    conn.close()
    return notifications

def get_user_shortcuts(username):
    conn = get_usersdb_connection()
    shortcuts = conn.execute('SELECT * FROM shortcuts WHERE user = ? ORDER BY name', 
                             (username,)).fetchall()
    conn.close()
    return shortcuts

def get_user_tasks(username):
    conn = get_usersdb_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user = ? ORDER BY due_date', 
                         (username,)).fetchall()
    conn.close()

    # Convertir la fecha a objeto datetime
    tasks = [
        {
            "id": task["id"],
            "user": task["user"],
            "description": task["description"],
            "due_date": datetime.strptime(task["due_date"], '%Y-%m-%d')
        }
        for task in tasks
    ]
    
    return tasks

def add_user_task(username, task_description, task_due_date):
    conn = get_usersdb_connection()
    conn.execute('INSERT INTO tasks (user, description, due_date) VALUES (?, ?, ?)',
                 (username, task_description, task_due_date.strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()


def get_favorite_documents(username):
    conn = get_usersdb_connection()
    documents = conn.execute('SELECT * FROM favorite_documents WHERE user = ? ORDER BY filename', 
                             (username,)).fetchall()
    conn.close()
    return documents

def get_shared_documents(username):
    conn = get_usersdb_connection()
    documents = conn.execute('SELECT * FROM shared_documents WHERE shared_with = ? ORDER BY filename', 
                             (username,)).fetchall()
    conn.close()
    return documents

def get_user_events(username):
    conn = get_usersdb_connection()
    events = conn.execute('SELECT * FROM events WHERE user = ? ORDER BY start_date', 
                          (username,)).fetchall()
    conn.close()
    return events

def submit_feedback(username, feedback):
    conn = get_usersdb_connection()
    conn.execute('INSERT INTO feedback (user, feedback, date) VALUES (?, ?, ?)', 
                 (username, feedback, datetime.now()))
    conn.commit()
    conn.close()
