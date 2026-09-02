import os
from flask import Flask, request
from flask_cors import CORS
from auth import auth
from operator import operator
from configdb import credentials

SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config.from_object(credentials)

app.register_blueprint(auth)
app.register_blueprint(operator)

@app.route('/')
def welcome():
    return "¡Bienvenido!"

def user_has_role():
    role = getattr(request, 'role', None)
    if role == 'usuario':
        return True

    return False
