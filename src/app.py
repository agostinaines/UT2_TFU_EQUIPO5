import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from configdb import credentials, get_connection
import bcrypt
import jwt
from encrypt import hash_pwd
from datetime import datetime, timedelta, timezone
import time as tmodule
import random
import threading

SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config.from_object(credentials)

@app.route('/')
def welcome():
    return "¡Bienvenido!"

def user_has_role():
    role = getattr(request, 'role', None)
    if role == 'usuario':
        return True

    return False

@app.route('/register', methods=['POST'])
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

@app.route('/login', methods=['POST'])
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

@app.route('/allSensors', methods=['GET'])
def get_all_sensors():
    try:
        connection = get_connection(user_has_role)
        cursor = connection.cursor()
        cursor.execute("SELECT id, activo, roto FROM sensor")
        results = cursor.fetchall()

        sensors = []
        for row in results:
            sensors.append({
                'id': row['id'],
                'activo': row['activo'],
                'roto': row['roto']
            })

        return jsonify({
            'success': True,
            'sensors': sensors
        }), 200
    except Exception as ex:
        return jsonify({
            'success': False,
            'description': 'Error',
            'error': str(ex)
        }), 500

@app.route('/allLogs', methods=['GET'])
def get_all_sensors_logs():
    """
    Consigue todos los registros de todos los sensores.
    """
    try:
        connection = get_connection(user_has_role)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sensor_logs")
        results = cursor.fetchall()

        logs = []
        for row in results:
            logs.append({
                'id': row['id'],
                'sensor_id': row['sensor_id'],
                'lectura': row['lectura']
            })

        cursor.close()
        connection.close()

        return jsonify({
            'logs': logs, 
            'success': True
        }), 200

    except Exception as ex:
        return jsonify({
            'success': False, 
            'description': 'Error', 
            'error': str(ex)
        }), 500

@app.route('/sensor/<id>/logs', methods=['GET'])
def get_sensor_logs(id):
    """
    Consigue todos los registros de un sensor en específico.
    """
    try:
        connection = get_connection(user_has_role)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sensor_logs sL WHERE sL.sensor_id = %s", id)
        results = cursor.fetchall()

        logs = []
        for row in results:
            logs.append({
                'id': row['id'],
                'lectura': row['lectura']
            })

        cursor.close()
        connection.close()

        return jsonify({
            'logs': logs, 
            'success': True
        }), 200

    except Exception as ex:
        return jsonify({
            'success': False, 
            'description': 'Error', 
            'error': str(ex)
        }), 500

@app.route('/newSensor', methods=['POST'])
def new_sensor():
    """
    Inserta un nuevo sensor.
    """
    try:
        body = request.get_json()
        version = body.get('version')
        if not version:
            return jsonify({
                'success': False,
                'description': 'Faltan datos obligatorios'
            }), 400

        connection = get_connection(user_has_role)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO sensor (version) VALUES (%s);", version)
        connection.commit()

        return jsonify({
            'success': True, 
            'description': 'Nuevo sensor registrado'
        }), 201

    except Exception as ex:
        if connection is not None:
            connection.rollback()
        
            return jsonify({
                'success': False,
                'description': 'Error',
                'error': str(ex)
            }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

@app.route('/toggle/<id>', methods=['PATCH'])
def toggle_sensor(id):
    """
    Activa o desactiva un sensor.
    """
    try:
        connection = get_connection(user_has_role)
        cursor = connection.cursor()

        cursor.execute(
            "SELECT activo FROM sensor WHERE id = %s",
            (id,)
        )

        sensor = cursor.fetchone()

        if sensor is None:
            cursor.close()
            connection.close()
            return jsonify({
                'success': False,
                'description': f'No existe el sensor {id}'
            })

        isActive = sensor['activo']

        if isActive:
            cursor.execute(
                "UPDATE sensor SET activo = FALSE WHERE id = %s",
                (id,)
            )
            description = 'Sensor apagado'
        else:
            cursor.execute(
                "UPDATE sensor SET activo = TRUE WHERE id = %s",
                (id,)
            )
            description = 'Sensor prendido'

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'description': description
        }), 200
    except Exception as ex:
        return jsonify({
            'success': False,
            'description': 'Error',
            'error': str(ex)
        }), 500

@app.route('/repairSensor/<id>', methods=['PATCH'])
def repair_sensor(id):
    """
    Simulamos el tiempo que lleva reparar un sensor dañado.
    """
    try:
        tmodule.sleep(30)
        connection = get_connection(user_has_role)
        cursor = connection.cursor()
        
        cursor.execute("UPDATE sensor SET roto = FALSE WHERE id = %s", (id,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'description': f'Sensor {id} reparado con éxito'
        }), 200
    except Exception as ex:
        return jsonify({
            'success': True,
            'description': 'Error',
            'error': str(ex)
        }), 500
    
def loadSensors():
    """
    Consulta los sensores guardados en la base de datos y los devuelve.
    """
    with get_connection(True) as connection:
        with connection.cursor() as cursor:
            sql = "SELECT s.id FROM sensor s WHERE s.activo = TRUE AND s.roto = FALSE;"
            cursor.execute(sql)
            sensors = cursor.fetchall()

            sensorsFormatted = []
            for sensor in sensors:
                sensorsFormatted.append(sensor['id'])

    return sensorsFormatted

def sensorReadings():
    """
    Simula la lectura de los sensores activos del sistema. Cada uno devuelve un número entre 0.0 y 1 cada 30 segundos.
    Si se detecta una lectura igual a 1 el sensor es considerado dañado y se imprime una alerta en la terminal.
    """
    while True:
        sensors = loadSensors()
        
        print(" ")
        for sensor in sensors:
            now = datetime.now()
            nowFormatted = now.strftime("%Y-%m-%d %H:%M:%S")

            reading = random.random()

            with get_connection(True) as connection:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO sensor_logs (sensor_id, lectura) VALUES (%s, %s)"
                    cursor.execute(sql, (sensor, reading,))
                connection.commit()

            print(f"-SENSOR: {sensor}. -LECTURA: {reading}. -TIEMPO: {nowFormatted}.", flush=True)

            if reading >= 0.99:
                with get_connection(True) as connection:
                    with connection.cursor() as cursor:
                        sql = "UPDATE sensor SET roto = TRUE, activo = FALSE WHERE id = %s"
                        cursor.execute(sql, (sensor,))

                        print(f"SENSOR {sensor} ESTÁ DAÑADO. ENVIAR TICKET DE REPARACIÓN.", flush=True)
                    connection.commit()          

        tmodule.sleep(10)

def start_background_tasks():
    thread = threading.Thread(target=sensorReadings, daemon=True)
    thread.start()

start_background_tasks()