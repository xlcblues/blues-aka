import os
from datetime import timedelta
from functools import lru_cache
from typing import List, Optional

from pydantic.v1 import BaseSettings, Field


class BaseConfig(BaseSettings):
    """基础配置类"""

    # 基础配置
    SECRET_KEY: str = "blues-aka"
    DEBUG: bool = False

    # 数据库配置
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # JWT配置
    JWT_SECRET_KEY: str = Field(
        default="jwt-secret-string",
        env="JWT_SECRET_KEY",
        description="JWT密钥，生产环境必须设置"
    )
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=7)
    JWT_TOKEN_LOCATION: List[str] = ['headers']

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # CORS配置
    CORS_ORIGINS: List[str] = []

    # 默认模型配置
    default_api_key: str= Field(
        default="",
        description="模型默认api必须设置"
    )

    default_api_base: str = Field(
        default="",
        description="模型默认url"
    )

    default_model: str = Field(
        default="",
        description="默认使用的LLM大模型"
    )

    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="默认模型温度，调整模型输出内容的随机性"
    )

    default_max_token: Optional[int] = Field(
        default=None,
        description="模型默认最大token数"
    )

    default_streaming: bool = Field(
        default=True,
        description="是否支持流式输出"
    )

    # 默认Agent设置
    agent_max_iterations: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Agent最大迭代次数"
    )

    agent_max_execution_time: Optional[float] = Field(
        default=None,
        description="Agent最大执行时间"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True

class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = "postgresql://postgres:123456@localhost:5432/postgres"
    LOG_LEVEL: str = "DEBUG"

class ConfigFactory:
    """配置工厂类"""

    _configs = {
        'Dev': DevelopmentConfig,
    }

    @classmethod
    @lru_cache
    def get_config(cls, env_name: str = None) -> BaseConfig:
        """获取配置实例（使用缓存避免重复加载）"""
        env_name = env_name or os.environ.get('FLASK_CONFIG', 'Dev')

        if env_name not in cls._configs:
            raise ValueError(f"Unknown environment: {env_name}")

        config_class = cls._configs[env_name]
        return config_class()

# 向后兼容的配置字典
config = {
    "Dev": DevelopmentConfig,
}