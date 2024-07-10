import sqlite3

def clear_table(table_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {table_name}')
    conn.commit()
    conn.close()
    print(f'Table {table_name} has been cleared.')

if __name__ == '__main__':
    tables_to_clear = ['notifications', 'documents', 'shared_files']
    for table in tables_to_clear:
        clear_table(table)
