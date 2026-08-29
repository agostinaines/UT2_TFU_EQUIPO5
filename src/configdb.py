import os

import pymysql
from dbutils.pooled_db import PooledDB

class DataBaseConfig:
    DEBUG = True
    MYSQL_HOST = os.getenv("MYSQL_HOST", "ADADB")
    MYSQL_DB = os.getenv("MYSQL_DB", "ADATFUDOS")
    MYSQL_USER = os.getenv("MYSQL_USER", '')
    MYSQL_PW = os.getenv("MYSQL_PW", '1234')

configuration = {
    "development": DataBaseConfig
}

credentials = configuration['development']

POOL = PooledDB(
    creator=pymysql,
    maxconnections=6,
    mincached=2,
    host=credentials.MYSQL_HOST,
    user=credentials.MYSQL_USER,
    password=credentials.MYSQL_PW,
    database=credentials.MYSQL_DB,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

def get_connection():
    return POOL.connection()