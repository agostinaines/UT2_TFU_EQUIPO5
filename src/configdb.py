import os
import pymysql
from dbutils.pooled_db import PooledDB

class DataBaseConfig:
    DEBUG = True
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_DB = os.getenv("MYSQL_DB", "tfu2")
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

POOL_UNKNOWN = PooledDB(
    creator=pymysql,
    maxconnections=3,
    mincached=0,
    host=credentials.MYSQL_HOST,
    user=credentials.MYSQL_USERS['unknown']['user'],
    password=credentials.MYSQL_USERS['unknown']['password'],
    database=credentials.MYSQL_DB,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

POOL_USER = PooledDB(
    creator=pymysql,
    maxconnections=3,
    mincached=0,
    host=credentials.MYSQL_HOST,
    user=credentials.MYSQL_USERS['usuario']['user'],
    password=credentials.MYSQL_USERS['usuario']['password'],
    database=credentials.MYSQL_DB,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

def get_connection(is_logged_in: bool):
    pool = POOL_USER if is_logged_in else POOL_UNKNOWN
    return pool.connection()