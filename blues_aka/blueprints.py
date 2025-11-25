from user import user_bp

# 注册蓝图
def init_blueprints(app):
    app.register_blueprint(user_bp)