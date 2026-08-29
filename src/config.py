import os

class DevelopmentConfig:
    DEBUG = True
    MYSQL_HOST = os.getenv("MYSQL_HOST", "db")
    MYSQL_DB = os.getenv("MYSQL_DB", "ObligatorioBDD")

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
    "development": DevelopmentConfig
}