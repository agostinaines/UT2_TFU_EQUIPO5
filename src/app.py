from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from encrypt import hash_pwd
from config import config
from db import connection
from functools import wraps
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSONIFY_MIMETYPE'] = "application/json; charset=utf-8"


@app.after_request
def set_charset(response):
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

app.config.from_object(config['development'])
SECRET_KEY = 'JWT_SECRET_KEY=dIeocMZ1BzPxMcgmkLLPweME31lpx4XP3bsAXpqgt3SLrpKF2a0X6cdUOYr7joIJQwgcL1ht3GFpijm8qFcm4pHyAjie0rCpWEbqUEyYB4W5p36YjqYLhykwjIctJmcoQwF7R8uL9Z3eC34jlgki9dA57EuzT06E6gamcrHbJSmYykfkDwOE5uEeerYGQqzKBFOw9esDhiC1g0v0gWtTcDEPbbg6XMlxhe4MKgZsTfyb7rvUyLRYITcFykegU2tCZDKY'

def user_has_role(*allowed_roles):
    """
    Devuelve True si el usuario autenticado tiene
    al menos uno de los roles pasados.
    """
    roles = getattr(request, 'roles', None)
    if roles is None:
        role = getattr(request, 'role', None)
        roles = [role] if role else []
    return any(r in roles for r in allowed_roles)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({
                'success': False,
                'description': 'Token requerido'
            }), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])


            request.role = data.get('role', 'unknown')


            request.roles = data.get(
                'roles',
                [request.role] if request.role else ['unknown']
            )

            request.ci = data['ci']

        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'description': 'El token ha expirado'
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'description': 'Token inválido'
            }), 401

        return f(*args, **kwargs)
    return decorated

def check_user_is_active(ci, role):
    conn = connection(role)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT isActive
            FROM user
            WHERE ci = %s
        """, (ci,))
        row = cursor.fetchone()

        if not row:
            return False, "Usuario no encontrado"
        if not row["isActive"]:
            return False, "Usuario inactivo"

        return True, None
    finally:
        cursor.close()
        conn.close()

# Registro de usuario
@app.route('/register', methods=['POST'])
def postRegister():
    try:
        data = request.get_json()

        nombre = data.get('nombre')
        nombre = nombre.replace(' ', '')
        apellido = data.get('apellido')
        apellido = apellido.replace(' ', '')
        mail = data.get('mail')
        contrasenia = data.get('contrasenia')
        confirmarContrasenia = data.get('confirmarContrasenia')

        if not all([nombre, apellido, mail, contrasenia, confirmarContrasenia]):
            return jsonify({
                'success': False,
                'description': 'Faltan datos obligatorios'
            }), 400
        if contrasenia != confirmarContrasenia:
            return jsonify({
                'success': False,
                'description': 'Las contraseñas deben coincidir'
            }), 400

        if len(contrasenia) <= 8:
            return jsonify({
                'success': False,
                'description': 'La contraseña es muy corta (mínimo 9 caracteres)'
            }), 400
        conn = connection()
        cursor = conn.cursor()

        if len(nombre) < 3 or not nombre.isalpha():
            return jsonify({
                'success': False,
                'description': 'Formato de nombre invalido'
            }), 400

        if len(apellido) < 3 or not apellido.isalpha():
            return jsonify({
                'success': False,
                'description': 'Formato de apellido invalido'
            }), 400

        conn = connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM usuario WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({
                'success': False,
                'description': 'El correo electrónico ya está en uso'
            }), 409

        passwordHash = hash_pwd(contrasenia)

        cursor.execute(
            "INSERT INTO usuario (mail, nombre, apellido) VALUES (%s, %s, %s, %s)",
            (mail, nombre, apellido)
        )

        cursor.execute(
            "INSERT INTO login (mail, contrasenia) VALUES (%s, %s)",
            (mail, passwordHash)
        )

        conn.commit()
        cursor.close()

        return jsonify({
            'success': True,
            'description': 'Usuario registrado correctamente'
        }), 201

    except Exception as ex:
        conn.rollback()
        print("ERROR EN /register:", ex)
        return jsonify({
            'success': False,
            'description': 'Error al registrar el usuario',
            'error': str(ex)
        }), 500