import sqlite3

def get_usersdb_connection():
    conn = sqlite3.connect('users.db', timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def alter_feedback_table():
    conn = get_usersdb_connection()
    cursor = conn.cursor()
    
    # Añadir la nueva columna 'capture'
    cursor.execute('DELETE FROM feedback')
    
    conn.commit()
    conn.close()

alter_feedback_table()
