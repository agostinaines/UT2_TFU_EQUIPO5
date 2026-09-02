import os
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from configdb import get_connection
from main import user_has_role
from encrypt import hash_pwd
import bcrypt
import jwt

auth = Blueprint("auth", __name__)

SECRET_KEY = os.getenv("SECRET_KEY")

@auth.route('/register', methods=['POST'])
def postRegister():
    try:
        body = request.get_json()

        nombre = body.get('nombre')
        apellido = body.get('apellido')
        mail = body.get('mail')
        contrasenia = body.get('contrasenia')
        confirmarContrasenia = body.get('confirmarContrasenia')

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
                'description': 'La contraseña debe ser de un mínimo de 9 caracteres'
            }), 400

        if len(nombre) < 3 or not nombre.isalpha():
            return jsonify({
                'success': False,
                'description': 'Formato de nombre inválido'
            }), 400

        if len(apellido) < 3 or not apellido.isalpha():
            return jsonify({
                'success': False,
                'description': 'Formato de apellido inválido'
            }), 400

        connection = get_connection(user_has_role())
        cursor = connection.cursor()

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

        connection.commit()

        return jsonify({
            'success': True,
            'description': 'Usuario registrado correctamente'
        }), 201

    except Exception as ex:
        if connection is not None:
            connection.rollback()

        return jsonify({
            'success': False,
            'description': 'Error al registrar el usuario',
            'error': str(ex)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

@auth.route('/login', methods=['POST'])
def postLogin():
    try:
        body = request.get_json()
        mail = body.get('mail')
        contrasenia = body.get('contrasenia')

        if not mail or not contrasenia:
            return jsonify({
                'success': False,
                'description': 'Faltan email o contraseña'
            }), 400

        connection = get_connection(user_has_role)
        cursor = connection.cursor()

        cursor.execute("SELECT mail FROM usuario WHERE mail = %s", (mail,))
        user_row = cursor.fetchone()

        if not user_row:
            cursor.close()
            connection.close()
            return jsonify({
                "success": False,
                "description": "Usuario no encontrado"
            }), 404

        mail = user_row["mail"]
        cursor.execute("SELECT contrasenia FROM login WHERE mail = %s", (mail,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'description': 'Credenciales inválidas'}), 401

        stored_hash = result['contrasenia']
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode()

        if not bcrypt.checkpw(contrasenia.encode(), stored_hash):
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'description': 'Credenciales inválidas'}), 401

        roles = []

        cursor.execute("SELECT rol FROM usuario WHERE mail = %s", (mail,))
        if cursor.fetchone():
            roles.append("operador")

        if not roles:
            roles = ["unknown"]

        now = datetime.now(timezone.utc)
        access_payload = {
            'mail': mail,
            'roles': roles,
            'exp': now + timedelta(minutes=120)
        }

        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')

        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'access_token': access_token,
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
