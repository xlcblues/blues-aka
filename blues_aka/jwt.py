from flask_jwt_extended import JWTManager

# 初始化jwt
def init_jwt(app):
    jwt = JWTManager(app)
    jwt.init_app(app)