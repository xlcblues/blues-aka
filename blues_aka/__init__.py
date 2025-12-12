import logging

from flask import Flask

from blues_aka.blueprints import init_blueprints
from blues_aka.config import config
from .extensions import init_extensions
from .logger import init_logger


def create_app(config_name):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "blues-aka"
    app.config.from_object(config[config_name])
    init_extensions(app)
    init_blueprints(app)
    init_logger(app)
    return app
