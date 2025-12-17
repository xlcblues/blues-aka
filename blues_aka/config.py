import os
from datetime import timedelta


class Dev:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:123456@localhost:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers']

class Prod:
    pass

config = {
    "Dev": Dev,
    "Prod": Prod
}