import logging

from flask import Flask

from blues_aka.blueprints import init_blueprints
from blues_aka.config import config
from .config.config import ConfigFactory
from .extensions import init_extensions
from .jwt import init_jwt
from .logger import init_logger


def create_app(config_name):
    app = Flask(__name__)
    config = ConfigFactory.get_config(config_name)
    app.config.update(config.dict())
    init_extensions(app)
    init_blueprints(app)
    init_logger(app)
    init_jwt(app)
    return app
