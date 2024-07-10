import sqlite3

def print_shared_files(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT filename, owner, shared_with, shared_type 
        FROM shared_files 
        WHERE shared_with = ?
    ''', (username,))
    
    shared_files = cursor.fetchall()
    
    print(f"Archivos compartidos con {username}:")
    for file in shared_files:
        print(f"Filename: {file[0]}, Owner: {file[1]}, Shared With: {file[2]}, Shared Type: {file[3]}")
    
    conn.close()

# Llamar a la función para el usuario "oim"
print_shared_files('oim')
