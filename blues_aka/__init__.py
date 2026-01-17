import atexit
import logging

from flask import Flask

from blues_aka.blueprints import init_blueprints
from blues_aka.config import config
from .config.config import ConfigFactory
from .extensions import init_extensions
from .jwt import init_jwt
from .logger import init_logger
from blues_aka.common.exceptionHandles import register_error_handlers
from blues_aka.tasks import init_scheduler

def create_app(config_name):
    app = Flask(__name__)
    config = ConfigFactory.get_config(config_name)
    app.config.update(config.dict())
    init_extensions(app)
    init_blueprints(app)
    init_logger(app)
    init_jwt(app)
    register_error_handlers(app)

    # 初始化定时任务调度器
    init_scheduler(app)

    # 注册应用关闭时的清理函数
    atexit.register(lambda: scheduler_shutdown())

    return app

def scheduler_shutdown():
    """应用关闭时清理调度器"""
    try:
        from blues_aka.tasks.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception as e:
        logging.getLogger(__name__).error(f"关闭调度器时出错: {str(e)}")
