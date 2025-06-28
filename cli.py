import requests
import json # Para imprimir de forma más legible las respuestas JSON

# URL base de la API Flask
API_BASE_URL = "http://127.0.0.1:5000/api"

# Usar una sesión de requests para manejar cookies automáticamente
session = requests.Session()

def display_response(response):
    """Muestra la respuesta JSON de la API de forma legible."""
    print("\nRespuesta de la API:")
    try:
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except requests.exceptions.JSONDecodeError:
        print(response.text)
    print("-" * 30)

def registrar_usuario():
    print("\n--- Registrar Nuevo Usuario ---")
    usuario = input("Nombre de usuario: ")
    contrasena = input("Contraseña: ")
    payload = {"usuario": usuario, "contraseña": contrasena}
    try:
        response = session.post(f"{API_BASE_URL}/registro", json=payload)
        display_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al registrar: {e}")

def iniciar_sesion():
    global session # Aseguramos que usamos la sesión global para que las cookies se guarden
    print("\n--- Iniciar Sesión ---")
    usuario = input("Nombre de usuario: ")
    contrasena = input("Contraseña: ")
    payload = {"usuario": usuario, "contraseña": contrasena}
    try:
        response = session.post(f"{API_BASE_URL}/login", json=payload)
        display_response(response)
        if response.status_code == 200:
            print("\n<html><body><h1>Bienvenido</h1></body></html>\n") # Mensaje HTML solicitado
            return True # Login exitoso
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al iniciar sesión: {e}")
    return False # Login fallido

def cerrar_sesion():
    global session
    print("\n--- Cerrar Sesión ---")
    try:
        response = session.post(f"{API_BASE_URL}/logout") # Envía cookies de sesión automáticamente
        display_response(response)
        # Restablecer la sesión para eliminar cookies y cualquier estado anterior
        session = requests.Session()
        print("Sesión cerrada localmente.")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al cerrar sesión: {e}")
    return True # Siempre vuelve al menú principal

def listar_tareas():
    print("\n--- Listar Tareas ---")
    try:
        response = session.get(f"{API_BASE_URL}/tareas")
        if response.status_code == 200:
            tareas = response.json()
            if tareas:
                print("Tus tareas:")
                for tarea in tareas:
                    estado = "Completada" if tarea.get('completada') else "Pendiente"
                    print(f"  ID: {tarea.get('id')}, Descripción: \"{tarea.get('descripcion')}\", Estado: {estado}")
            else:
                print("No tienes tareas.")
        else:
            display_response(response) # Mostrar error si no es 200 (ej. 401 no autorizado)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al listar tareas: {e}")

def agregar_tarea():
    print("\n--- Agregar Tarea ---")
    descripcion = input("Descripción de la tarea: ")
    if not descripcion.strip():
        print("La descripción no puede estar vacía.")
        return
    payload = {"descripcion": descripcion.strip()}
    try:
        response = session.post(f"{API_BASE_URL}/tareas", json=payload)
        display_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al agregar tarea: {e}")

def eliminar_tarea():
    print("\n--- Eliminar Tarea ---")
    try:
        id_tarea = int(input("ID de la tarea a eliminar: "))
    except ValueError:
        print("ID inválido. Debe ser un número.")
        return

    try:
        response = session.delete(f"{API_BASE_URL}/tareas/{id_tarea}")
        display_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al eliminar tarea: {e}")

def menu_autenticado():
    while True:
        print("\n--- Menú Principal (Autenticado) ---")
        print("1. Listar tareas")
        print("2. Agregar tarea")
        print("3. Eliminar tarea")
        # Podríamos añadir "Actualizar estado de tarea" aquí si se implementa en API y CLI
        print("4. Logout")
        opcion = input("Elige una opción: ")

        if opcion == '1':
            listar_tareas()
        elif opcion == '2':
            agregar_tarea()
        elif opcion == '3':
            eliminar_tarea()
        elif opcion == '4':
            cerrar_sesion()
            break # Salir del menú autenticado y volver al menú inicial
        else:
            print("Opción no válida.")

def menu_inicial():
    while True:
        print("\n--- Bienvenido al Gestor de Tareas CLI ---")
        print("1. Registrarse")
        print("2. Iniciar Sesión")
        print("3. Salir")
        opcion = input("Elige una opción: ")

        if opcion == '1':
            registrar_usuario()
        elif opcion == '2':
            if iniciar_sesion():
                menu_autenticado() # Entrar al menú de usuario si el login es exitoso
        elif opcion == '3':
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    # Verificar si la API está corriendo (opcional, pero útil para el usuario)
    try:
        # Hacemos una petición a una ruta que no requiera login, ej. /api/login (aunque sea POST)
        # o podríamos añadir una ruta /api/health a la app Flask.
        # Por ahora, asumimos que el usuario la tiene corriendo.
        pass
    except requests.exceptions.ConnectionError:
        print(f"ERROR: No se pudo conectar a la API en {API_BASE_URL}.")
        print("Asegúrate de que el servidor Flask (app.py) está corriendo.")
        exit(1)

    menu_inicial()
