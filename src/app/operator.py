from flask import Blueprint, jsonify, request
from main import user_has_role
from configdb import get_connection

operator = Blueprint("operator", __name__)

@operator.route('/allLogs', methods=['GET'])
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
                'lectura': row['lectura'],
                'fecha_hora': row['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S")
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

@operator.route('/sensor/<id>/logs', methods=['GET'])
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
                'lectura': row['lectura'],
                'fecha_hora': row['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S")
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

@operator.route('/newSensor', methods=['POST'])
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

@operator.route('/toggle/<id>', methods=['PATCH'])
def toggle_sensor(id):
    """
    Activa o desactiva un sensor.
    """
    try:
        body = request.get_json()
        sensor_id = body.get('sensor_id')

        if not sensor_id:
            return jsonify({
                'success': False, 
                'description': 'Faltan datos obligatorios'
            }), 400

        connection = get_connection(user_has_role)
        cursor = connection.cursor()

        cursor.execute("SELECT s.activo FROM sensor s WHERE s.id = %s", id)
        isActive = cursor.fetchone()

        if isActive['activo']:
            cursor.execute("UPDATE sensor s SET s.activo = FALSE")
            connection.commit()
        else:
            cursor.execute("UPDATE sensor s SET s.activo = TRUE")
            connection.commit()

        cursor.close()
        connection.close()
    except Exception as ex:
        return jsonify({
            'success': False,
            'description': 'Error',
            'error': str(ex)
        }), 500
