import sqlite3
from datetime import datetime

def create_tables():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Crear tabla de actividades recientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            description TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla de documentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            filename TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla de notificaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            message TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla de atajos personalizados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shortcuts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
    ''')
    
    # Crear tabla de tareas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            description TEXT NOT NULL,
            due_date DATE
        )
    ''')
    
    # Crear tabla de documentos favoritos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorite_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            filename TEXT NOT NULL
        )
    ''')
    
    # Crear tabla de documentos compartidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            shared_by TEXT NOT NULL,
            shared_with TEXT NOT NULL
        )
    ''')
    
    # Crear tabla de eventos de usuario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            title TEXT NOT NULL,
            start_date DATETIME,
            end_date DATETIME
        )
    ''')
    
    # Crear tabla de retroalimentación
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            feedback TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
create_tables()

