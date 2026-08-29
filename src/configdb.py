import os

class DataBaseConfig:
    DEBUG = True
    MYSQL_HOST = os.getenv("MYSQL_HOST", "ADADB")
    MYSQL_DB = os.getenv("MYSQL_DB", "ADATFUDOS")
    MYSQL_USER = os.getenv("MYSQL_USER", '')
    MYSQL_PW = os.getenv("MYSQL_PW", '1234')


configuration = {
    "development": DataBaseConfig
}