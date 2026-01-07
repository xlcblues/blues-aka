import logging
from typing import Optional, Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatZhipuAI
from blues_aka.config.config import ConfigFactory

logger = logging.getLogger(__name__)

# 获取配置实例
_config = ConfigFactory.get_config()

# 获取聊天模型
def get_chat_model(
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = None,
        **kwargs: Any
) -> BaseChatModel:

    model_name = model_name or _config.default_model
    temperature = temperature if temperature is not None else _config.default_temperature
    streaming = streaming if streaming is not None else _config.default_streaming

    model_config: Dict[str, Any] = {
        'model_name': model_name,
        'temperature': temperature,
        'streaming': streaming,
        'api_key': _config.default_api_key,
        'base_url': _config.default_api_base
    }

    if max_tokens is not None:
        model_config['max_tokens'] = max_tokens
    elif _config.default_max_token is not None:
        model_config['max_tokens'] = _config.default_max_token

    model_config.update(kwargs)

    try:
        model = ChatZhipuAI(**model_config)
        return model
    except Exception as e:
        logger.error(f"模型创建失败: {e}")
        raise

def get_streaming_model(
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
) -> BaseChatModel:
    return get_chat_model(model_name=model_name, temperature=temperature, streaming=True, **kwargs)

def getStructuredOutputModel(
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any
) -> BaseChatModel:
    return get_chat_model(model_name=model_name, temperature=temperature, streaming=False, **kwargs)

# 预定义的模型配置
MODEL_CONFIGS = {
    "default": {
        "model_name": "glm-4.5",
        "temperature": 0.7,
        "description": "默认模型，平衡性能和成本",
    },
    "fast": {
        "model_name": "glm-4.5-air",
        "temperature": 0.7,
        "description": "快速模型，适合简单任务",
    },
    "precise": {
        "model_name": "glm-4.6",
        "temperature": 0.3,
        "description": "精确模型，适合需要准确性的任务",
    },
    "creative": {
        "model_name": "glm-4.6",
        "temperature": 1.0,
        "description": "创意模型，适合需要创造性的任务",
    },
    "multimodal": {
        "model_name": "glm-4.5V",
        "temperature": 0.7,
        "description": "多模态模型，可以输入图片",
    },
}

def get_model_by_preset(preset: str = "default", **kwargs: Any) -> BaseChatModel:
    if preset not in MODEL_CONFIGS:
        available_models = MODEL_CONFIGS.values()
        raise ValueError(f"未知的预设: {preset}. 可用预设: {available_models}")

    config = MODEL_CONFIGS[preset].copy()
    config.pop("description", None)
    return get_chat_model(**config)

def get_model_string(
        model_name: Optional[str] = None,
        provider: str = "ZhiPuAI"
) -> str:
    model_name = model_name or _config.default_model
    model_string = f"{provider} : {model_name}"
    logger.info(model_string)
    return model_string
