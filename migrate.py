import sqlite3

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
