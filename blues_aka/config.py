import os

class Dev:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:123456@localhost:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  
class Prod:
    pass

config = {
    "Dev": Dev,
    "Prod": Prod
}