from .user.routes import user_bp, auth_bp
from .Agent.routes import agent_bp, conversation_bp, chat_bp
from blues_aka.tasks.routes import tasks_bp

# 注册蓝图
def init_blueprints(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(tasks_bp)