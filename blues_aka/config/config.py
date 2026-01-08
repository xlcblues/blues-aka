import os
from datetime import timedelta
from functools import lru_cache
from typing import List, Optional

from pydantic.v1 import BaseSettings, Field


class BaseConfig(BaseSettings):
    """基础配置类"""

    # 基础配置
    SECRET_KEY: str = Field(
        default="",
        env="SECRET_KEY",
        description="Flask 密钥，必须通过环境变量设置"
    )
    DEBUG: bool = False

    # 数据库配置
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="",
        env="DATABASE_URL",
        description="数据库连接字符串，必须通过环境变量设置"
    )
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

    # 智谱 AI API 配置
    default_api_key: str = Field(
        default="",
        env="ZHIPU_API_KEY",
        description="智谱AI API密钥，必须通过环境变量设置"
    )

    default_api_base: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        env="ZHIPU_API_BASE",
        description="智谱AI API地址"
    )

    default_model: str = Field(
        default="glm-4.5",
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
    LOG_LEVEL: str = "DEBUG"

class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG: bool = False
    # 生产环境额外配置
    LOG_LEVEL: str = "INFO"

class ConfigFactory:
    """配置工厂类"""

    _configs = {
        'Dev': DevelopmentConfig,
        'Prod': ProductionConfig,
    }

    @classmethod
    @lru_cache
    def get_config(cls, env_name: str = None) -> BaseConfig:
        """获取配置实例（使用缓存避免重复加载）"""
        env_name = env_name or os.environ.get('FLASK_CONFIG', 'Dev')

        if env_name not in cls._configs:
            raise ValueError(f"Unknown environment: {env_name}")

        config_class = cls._configs[env_name]

        config = config_class()

        # 验证必需的环境变量
        if not config.SQLALCHEMY_DATABASE_URI:
            raise ValueError(
                "数据库连接字符串(DATABASE_URL)环境变量是必需的。 "
                "请在.env文件中设置它。"
            )

        if not config.JWT_SECRET_KEY:
            raise ValueError(
                "JWT密钥(JWT_SECRET_KEY)环境变量是必需的。 "
                "请在.env文件中设置它。"
            )

        if not config.default_api_key:
            raise ValueError(
                "智谱API密钥(ZHIPU_API_KEY)环境变量是必需的。 "
                "请在.env文件中设置它。"
            )

        if len(config.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT密钥(JWT_SECRET_KEY)必须至少32个字符长。 "
                "请使用更强的密钥。"
            )

        return config



# 向后兼容的配置字典
config = {
    "Dev": DevelopmentConfig,
}