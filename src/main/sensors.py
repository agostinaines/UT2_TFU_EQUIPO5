import pymysql.cursors
import threading
import time
from random import random, randrange
import os
from dotenv import load_dotenv
from configdb import configuration

load_dotenv()

credentials = configuration['development']

broken = False
cantidadSensores = os.getenv("CANTIDAD_SENSORES", 4)

def isSensorBroken():
    sensorNumber = randrange(cantidadSensores)
    isBroken = random()

    if isBroken == 1:
        connection = pymysql.connect(host=credentials.MYSQL_HOST,
                             user=credentials.MYSQL_USER,
                             password=credentials.MYSQL_PW,
                             database=credentials.MYSQL_DB,
                             cursorclass=pymysql.cursors.DictCursor)

    with connection:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "INSERT INTO `users` (`email`, `password`) VALUES (%s, %s)"
            cursor.execute(sql, ('webmaster@python.org', 'very-secret'))

        connection.commit()


def sensorReadings():
    return 0