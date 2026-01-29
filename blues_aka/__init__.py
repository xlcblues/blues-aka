import atexit
import logging
import os

from flask import Flask, send_from_directory

from blues_aka.blueprints import init_blueprints
from blues_aka.config import config
from .config.config import ConfigFactory
from .extensions import init_extensions
from .jwt import init_jwt
from .logger import init_logger
from blues_aka.common.exceptionHandles import register_error_handlers
from blues_aka.tasks import init_scheduler

def create_app(config_name):
    app = Flask(__name__, static_folder=None)
    config = ConfigFactory.get_config(config_name)
    app.config.update(config.dict())
    init_extensions(app)

    # 配置前端静态文件服务（在注册API蓝图之前）
    setup_frontend_static(app)

    # 注册API蓝图
    init_blueprints(app)
    init_logger(app)
    init_jwt(app)
    register_error_handlers(app)

    # 初始化定时任务调度器
    init_scheduler(app)

    # 注册应用关闭时的清理函数
    atexit.register(lambda: scheduler_shutdown())

    return app

def setup_frontend_static(app):
    """配置前端静态文件服务和SPA路由支持"""
    # 获取前端构建目录
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')

    # 如果前端构建文件存在，提供静态文件服务
    if os.path.exists(frontend_dist):
        @app.route('/')
        @app.route('/agents')
        @app.route('/users')
        @app.route('/conversations')
        @app.route('/chat')
        @app.route('/profile')
        @app.route('/settings')
        @app.route('/login')
        @app.route('/register')
        def serve_frontend():
            """服务前端index.html文件"""
            return send_from_directory(frontend_dist, 'index.html')

        @app.route('/assets/<path:filename>')
        def serve_assets(filename):
            """服务前端静态资源"""
            return send_from_directory(os.path.join(frontend_dist, 'assets'), filename)

        # Catch-all路由：处理所有前端路由
        # 这个路由必须在最后注册，所以会在所有API路由之后匹配
        @app.route('/<path:path>')
        def serve_frontend_catchall(path):
            """
            Catch-all路由：服务前端应用
            对于API请求，会在之前的蓝图中被处理
            对于前端路由，返回index.html让Vue Router处理
            """
            # 检查是否是静态文件请求
            if path.startswith('assets/'):
                return send_from_directory(frontend_dist, path)

            # 对于其他所有路径，返回index.html（SPA路由fallback）
            return send_from_directory(frontend_dist, 'index.html')

        app.logger.info(f"前端静态文件服务已启用: {frontend_dist}")
    else:
        # 开发环境下，前端由Vite dev server提供服务
        app.logger.info(f"前端构建文件不存在: {frontend_dist}")
        app.logger.info("开发环境下请确保前端开发服务器正在运行 (npm run dev)")


def scheduler_shutdown():
    """应用关闭时清理调度器"""
    try:
        from blues_aka.tasks.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception as e:
        logging.getLogger(__name__).error(f"关闭调度器时出错: {str(e)}")
