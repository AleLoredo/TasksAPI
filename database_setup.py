import sqlite3

DATABASE_NAME = 'usuarios.db'

def crear_tabla_usuarios():
    """Crea la tabla de usuarios en la base de datos si no existe."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contrasena_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Tabla 'usuarios' creada o ya existente en '{DATABASE_NAME}'.")

def crear_tabla_tareas():
    """Crea la tabla de tareas en la base de datos si no existe."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            completada BOOLEAN NOT NULL DEFAULT 0,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Tabla 'tareas' creada o ya existente en '{DATABASE_NAME}'.")

if __name__ == '__main__':
    crear_tabla_usuarios()
    crear_tabla_tareas()
