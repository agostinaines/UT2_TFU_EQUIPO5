import time
import importlib.util
from datetime import datetime
from random import random

path = "../configdb.py"
mname = "configdb"

spec = importlib.util.spec_from_file_location(mname, path)
configuration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configuration)

def loadSensors():
    """
    Consulta los sensores guardados en la base de datos y los devuelve.
    """
    with configuration.get_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT s.id FROM sensor s WHERE s.activo = TRUE AND s.roto = FALSE"
            cursor.execute(sql)
            sensors = [row[0] for row in cursor.fetchall()]
    print(f"ESTOS SON LOS SENSORES: {sensors}")
    return sensors

def sensorReadings():
    """
    Simula la lectura de los sensores activos del sistema. Cada uno devuelve un número entre 0.0 y 1 cada 30 segundos.
    """
    # sensors = loadSensors()
    sensors = [0, 1, 2, 3]
    time.sleep(30)
    for sensor in sensors:
        now = datetime.now()
        nowFormatted = now.strftime("%Y-%m-%d %H:%M:%S")

        reading = random() # 0.0 a 1.0

        with configuration.get_connection() as connection:
            with connection.cursor() as cursor:
                sql = "INSERT INTO sensor_logs (sensor_id, lectura, log_fecha) VALUES (%s, %s, %s)"
                cursor.execute(sql, (sensor, reading, nowFormatted))

        print(f"-SENSOR: {sensor}. -LECTURA: {reading}. -TIEMPO: {nowFormatted}.")

        if reading == 1:
            with configuration.get_connection() as connection:
                with connection.cursor() as cursor:
                    sql = "UPDATE sensor SET roto = TRUE WHERE sensor.id = %s"
                    cursor.execute(sql, (sensor))
                    connection.commit()

if __name__ == "__main__":
    sensorReadings()