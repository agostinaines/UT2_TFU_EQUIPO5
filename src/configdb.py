import os

import pymysql
from dbutils.pooled_db import PooledDB

class DataBaseConfig:
    DEBUG = True
    MYSQL_HOST = os.getenv("MYSQL_HOST", "ADADB")
    MYSQL_DB = os.getenv("MYSQL_DB", "ADATFUDOS")
    MYSQL_USERS = {
        "unknown": {
            "user": os.getenv("MYSQL_UNKNOWN_USER", "unknown_user"),
            "password": os.getenv("MYSQL_UNKNOWN_PASSWORD", "Unknown19976543!"),
        },
        "usuario": {
            "user": os.getenv("MYSQL_USUARIO_USER", "usuario_user"),
            "password": os.getenv("MYSQL_USUARIO_PASSWORD", "Usuario19976543!"),
        },
    }

config = {
    "development": DataBaseConfig
}

credentials = config['development']

POOL = PooledDB(
    creator=pymysql,
    maxconnections=6,
    mincached=2,
    host=credentials.MYSQL_HOST,
    user=credentials.MYSQL_USERS['unknown']['user'],
    password=credentials.MYSQL_USERS['unknown']['password'],
    database=credentials.MYSQL_DB,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

def get_connection():
    return POOL.connection()