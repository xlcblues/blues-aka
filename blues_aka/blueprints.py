from .user.routes import user_bp, auth_bp

# 注册蓝图
def init_blueprints(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
