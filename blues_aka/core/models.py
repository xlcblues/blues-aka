import logging
from typing import Optional, Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatZhipuAI
from blues_aka.config import BaseConfig

logger = logging.getLogger(__name__)

# 获取聊天模型
def getChatModel(
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = None,
        **kwargs: Any
) -> BaseChatModel:

    model_name = model_name or BaseConfig.default_model
    temperature = temperature or BaseConfig.default_temperature
    streaming = streaming or BaseConfig.default_streaming

    model_config: Dict[str, Any] = {
        'model_name': model_name,
        'temperature': temperature,
        'streaming': streaming,
        'api-key': BaseConfig.default_api_key,
        'base-url': BaseConfig.default_api_base
    }

    if max_tokens is not None:
        model_config['max_tokens'] = max_tokens
    elif BaseConfig.default_max_token is not None:
        model_config['max_tokens'] = BaseConfig.default_max_token

    model_config.update(kwargs)

    try:
        model = ChatZhipuAI(**model_config)
        return model
    except Exception as e:
        logger.error(f"模型创建失败: {e}")
        raise

def getStreamingModel(
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
) -> BaseChatModel:
    return getChatModel(model_name=model_name, temperature=temperature, streaming=True, **kwargs)

def getStructuredOutputModel(
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any
) -> BaseChatModel:
    return getChatModel(model_name=model_name, temperature=temperature, streaming=False, **kwargs)

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

def getModelByPreset(preset: str = "default", **kwargs: Any) -> BaseChatModel:
    if preset not in MODEL_CONFIGS:
        available_models = MODEL_CONFIGS.values()
        raise ValueError(f"未知的预设: {preset}. 可用预设: {available_models}")

    config = MODEL_CONFIGS[preset].copy()
    config.pop("description", None)
    return getChatModel(**config)

def getModelString(
        model_name: Optional[str] = None,
        provider: str = "ZhiPuAI"
) -> str:
    model_name = model_name or BaseConfig.default_model
    model_string = f"{provider} : {model_name}"
    logger.info(model_string)
    return model_string
