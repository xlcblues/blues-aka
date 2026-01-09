
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cors = CORS()

def init_extensions(app):
    db.init_app(app)
    # 配置CORS,允许前端跨域访问
    cors.init_app(app, resources={
        r"/*": {
            "origins": ["http://localhost:3002", "http://localhost:3000", "http://localhost:3001"],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["X-Total-Count"],
            "supports_credentials": True,
            "max_age": 3600,
            "send_wildcard": False,
        }
    })