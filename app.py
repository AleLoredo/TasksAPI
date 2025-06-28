import sqlite3
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_super_secreto_aqui_cambialo_en_produccion_ urgente' # Necesario para Flask-Login y sesiones
DATABASE_NAME = 'usuarios.db'

login_manager = LoginManager()
login_manager.init_app(app)

# Esta función se llamará si un usuario no autenticado intenta acceder a una ruta protegida por @login_required
# En lugar de redirigir a una página de login HTML, devolvemos un error 401 JSON.
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify(error="Acceso no autorizado. Por favor, inicia sesión."), 401

class User(UserMixin):
    def __init__(self, id, usuario):
        self.id = id
        self.usuario = usuario

    @staticmethod
    def get(user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(id=user_data['id'], usuario=user_data['usuario'])
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(id=user_data['id'], usuario=user_data['usuario']), user_data['contrasena_hash']
        return None, None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- Endpoints de Autenticación API ---
@app.route('/api/registro', methods=['POST'])
def api_registro():
    datos = request.get_json()

    if not datos or 'usuario' not in datos or 'contraseña' not in datos:
        return jsonify({"error": "Faltan datos de usuario o contraseña"}), 400

    usuario = datos['usuario']
    contrasena = datos['contraseña']

    if not usuario or not contrasena:
        return jsonify({"error": "Usuario y contraseña no pueden estar vacíos"}), 400

    contrasena_hash = generate_password_hash(contrasena)
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO usuarios (usuario, contrasena_hash) VALUES (?, ?)",
                       (usuario, contrasena_hash))
        conn.commit()
        user_id = cursor.lastrowid
        return jsonify({"mensaje": "Usuario registrado exitosamente", "id": user_id}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"error": "El nombre de usuario ya existe"}), 409
    except Exception as e:
        conn.rollback()
        print(f"Error inesperado en registro API: {e}")
        return jsonify({"error": "Ocurrió un error durante el registro"}), 500
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    if current_user.is_authenticated:
        return jsonify({"mensaje": "Usuario ya autenticado", "usuario": current_user.usuario}), 200

    datos = request.get_json()
    if not datos or 'usuario' not in datos or 'contraseña' not in datos:
        return jsonify({"error": "Faltan datos de usuario o contraseña"}), 400

    username = datos['usuario']
    password = datos['contraseña']

    user_obj, stored_password_hash = User.get_by_username(username)

    if user_obj and stored_password_hash and check_password_hash(stored_password_hash, password):
        login_user(user_obj, remember=True) # remember=True es útil para sesiones más largas si la CLI las soporta
        return jsonify({"mensaje": "Inicio de sesión exitoso", "usuario": user_obj.usuario}), 200
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({"mensaje": "Sesión cerrada exitosamente"}), 200

@app.route('/api/status')
@login_required
def api_status():
    return jsonify({"autenticado": True, "usuario_id": current_user.id, "usuario": current_user.usuario})

# --- Endpoints de Tareas API ---

@app.route('/api/tareas', methods=['GET'])
@login_required
def api_listar_tareas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, descripcion, completada FROM tareas WHERE usuario_id = ?", (current_user.id,))
    tareas_data = cursor.fetchall()
    conn.close()

    tareas_list = [dict(row) for row in tareas_data]
    return jsonify(tareas_list), 200

@app.route('/api/tareas', methods=['POST'])
@login_required
def api_agregar_tarea():
    datos = request.get_json()
    if not datos or 'descripcion' not in datos or not datos['descripcion'].strip():
        return jsonify({"error": "La descripción de la tarea es requerida"}), 400

    descripcion = datos['descripcion'].strip()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tareas (descripcion, usuario_id, completada) VALUES (?, ?, ?)",
                       (descripcion, current_user.id, False)) # Nueva tarea por defecto no completada
        conn.commit()
        nueva_tarea_id = cursor.lastrowid
        # Devolver la tarea creada podría ser útil
        return jsonify({"mensaje": "Tarea agregada exitosamente", "id_tarea": nueva_tarea_id, "descripcion": descripcion, "completada": False}), 201
    except Exception as e:
        conn.rollback()
        print(f"Error inesperado al agregar tarea API: {e}")
        return jsonify({"error": "Ocurrió un error al agregar la tarea"}), 500
    finally:
        conn.close()

@app.route('/api/tareas/<int:id_tarea>', methods=['DELETE'])
@login_required
def api_eliminar_tarea(id_tarea):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Verificar que la tarea pertenece al usuario actual antes de eliminar
        cursor.execute("DELETE FROM tareas WHERE id = ? AND usuario_id = ?", (id_tarea, current_user.id))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"mensaje": "Tarea eliminada exitosamente"}), 200
        else:
            # No se encontró la tarea o no pertenece al usuario
            return jsonify({"error": "Tarea no encontrada o no tienes permiso para eliminarla"}), 404
    except Exception as e:
        conn.rollback()
        print(f"Error inesperado al eliminar tarea API: {e}")
        return jsonify({"error": "Ocurrió un error al eliminar la tarea"}), 500
    finally:
        conn.close()

@app.route('/api/tareas/<int:id_tarea>', methods=['PUT'])
@login_required
def api_actualizar_tarea(id_tarea):
    datos = request.get_json()
    if 'completada' not in datos or not isinstance(datos['completada'], bool):
        return jsonify({"error": "Se requiere el campo 'completada' (booleano)"}), 400

    nuevo_estado = datos['completada']

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tareas SET completada = ? WHERE id = ? AND usuario_id = ?",
                       (nuevo_estado, id_tarea, current_user.id))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"mensaje": "Estado de la tarea actualizado", "id_tarea": id_tarea, "completada": nuevo_estado}), 200
        else:
            return jsonify({"error": "Tarea no encontrada o no tienes permiso para actualizarla"}), 404
    except Exception as e:
        conn.rollback()
        print(f"Error inesperado al actualizar tarea API: {e}")
        return jsonify({"error": "Ocurrió un error al actualizar la tarea"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # No es necesario crear la carpeta 'templates' aquí ya que no se usa.
    # El script database_setup.py debe ejecutarse manualmente si es necesario.
    app.run(debug=True, host='0.0.0.0', port=5000)
