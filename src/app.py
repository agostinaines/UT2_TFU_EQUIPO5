from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from encrypt import hash_pwd
from configdb import config
from db import connection
from functools import wraps

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

            request.mail = data['mail']

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

def check_user_is_active(mail, role):
    conn = connection(role)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT *
            FROM usuario
            WHERE mail = %s
        """, (mail,))
        row = cursor.fetchone()

        if not row:
            return False, "Usuario no encontrado"
        return True, None
    finally:
        cursor.close()
        conn.close()

@app.route('/register', methods=['POST'])
def postRegister():
    conn = None
    cursor = None

    try:
        data = request.get_json()

        nombre = data.get('nombre')
        apellido = data.get('apellido')
        mail = data.get('mail')
        contrasenia = data.get('contrasenia')
        confirmarContrasenia = data.get('confirmarContrasenia')

        if not all([nombre, apellido, mail, contrasenia, confirmarContrasenia]):
            return jsonify({
                'success': False,
                'description': 'Faltan datos obligatorios'
            }), 400

        nombre = nombre.replace(' ', '')
        apellido = apellido.replace(' ', '')

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

        cursor.execute(
            "SELECT mail FROM usuario WHERE mail = %s",
            (mail,)
        )

        if cursor.fetchone():
            return jsonify({
                'success': False,
                'description': 'El correo electrónico ya está en uso'
            }), 409

        passwordHash = hash_pwd(contrasenia)

        cursor.execute(
            "INSERT INTO usuario (mail, nombre, apellido) VALUES (%s, %s, %s)",
            (mail, nombre, apellido)
        )

        cursor.execute(
            "INSERT INTO login (mail, contrasenia) VALUES (%s, %s)",
            (mail, passwordHash)
        )

        conn.commit()

        return jsonify({
            'success': True,
            'description': 'Usuario registrado correctamente'
        }), 201

    except Exception as ex:
        if conn is not None:
            conn.rollback()

        print("ERROR EN /register:", ex)

        return jsonify({
            'success': False,
            'description': 'Error al registrar el usuario',
            'error': str(ex)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

@app.route('/login', methods=['POST'])
def postLogin():
    try:
        data = request.get_json()
        mail = data.get('mail')
        contrasenia = data.get('contrasenia')

        if not mail or not contrasenia:
            return jsonify({
                'success': False,
                'description': 'Faltan email o contraseña'
            }), 400

        conn = connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT mail
            FROM usuario
            WHERE mail = %s
        """, (mail,))
        user_row = cursor.fetchone()

        if not user_row:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "description": "Usuario no encontrado"
            }), 404

        mail = user_row["mail"]

        cursor.execute("SELECT contrasenia FROM login WHERE mail = %s", (mail,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'description': 'Credenciales inválidas'}), 401

        stored_hash = result['contrasenia']
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode()

        if not bcrypt.checkpw(contrasenia.encode(), stored_hash):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'description': 'Credenciales inválidas'}), 401

        roles = []

        cursor.execute("SELECT rol FROM usuario WHERE mail = %s", (mail,))
        if cursor.fetchone():
            roles.append("operador")

        if not roles:
            roles = ["unknown"]

        prioridad = ['operador']
        main_role = next((r for r in prioridad if r in roles), roles[0])

        now = datetime.now(timezone.utc)
        access_payload = {
            'mail': mail,
            'role': main_role,
            'roles': roles,
            'exp': now + timedelta(minutes=120)
        }

        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'access_token': access_token,
            'role': main_role,
            'roles': roles,
            'description': 'Login correcto'
        }), 200

    except Exception as ex:
        print("ERROR EN /login:", ex)
        return jsonify({
            'success': False,
            'description': 'Error en el login',
            'error': str(ex)
        }), 500

@app.route('/sensor/log', methods=['GET'])
def getSensorLogs():
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensor_logs")
        results = cursor.fetchall()
        cursor.close()

        sensor = []
        for row in results:
            sensor.append({
                'id': row['id'],
                'sensor_id': row['sensor_id'],
                'lectura': row['lectura'],
                'fecha_hora': row['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({'sensor': sensor, 'success': True}), 200

    except Exception as ex:
        return jsonify({'success': False, 'description': 'Error', 'error': str(ex)}), 500