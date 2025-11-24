import os
from flask import Flask
from blues_aka.config import config

def create_app(config_name):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "blues-aka"
    app.config.from_object(config[config_name])
    return app
