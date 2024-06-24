import sqlite3

def get_db_connection():
    conn = sqlite3.connect('auditoria.db', timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def alter_auditoria_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add the new column 'accion' with a default value
    cursor.execute('ALTER TABLE auditoria ADD COLUMN accion TEXT DEFAULT "unknown"')
    
    # Create a new table with the updated schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditoria_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_subida TEXT NOT NULL,
            accion TEXT NOT NULL,
            documento TEXT NOT NULL,
            autor TEXT NOT NULL,
            version TEXT NOT NULL
        )
    ''')

    # Copy the data from the old table to the new table
    cursor.execute('''
        INSERT INTO auditoria_new (id, fecha_subida, accion, documento, autor, version)
        SELECT id, fecha_subida, accion, documento, autor, version
        FROM auditoria
    ''')

    # Drop the old table
    cursor.execute('DROP TABLE auditoria')

    # Rename the new table to the old table name
    cursor.execute('ALTER TABLE auditoria_new RENAME TO auditoria')

    conn.commit()
    conn.close()
alter_auditoria_table()


