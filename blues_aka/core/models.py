"""
AI模型管理模块

本模块提供了AI聊天模型的创建、配置和管理功能。基于智谱AI(GlM)系列模型,
提供了多种便捷的模型获取方式和预设配置。

主要功能:
    - get_chat_model: 获取配置好的聊天模型实例
    - get_streaming_model: 获取流式输出的聊天模型
    - getStructuredOutputModel: 获取结构化输出的聊天模型
    - get_model_by_preset: 根据预设配置获取模型
    - get_model_string: 获取模型信息字符串

预设模型配置:
    - default: 默认模型,平衡性能和成本
    - fast: 快速模型,适合简单任务
    - precise: 精确模型,适合需要准确性的任务
    - creative: 创意模型,适合需要创造性的任务
    - multimodal: 多模态模型,支持图片输入

模块依赖:
    - langchain_core: LangChain核心功能
    - langchain_community: LangChain社区集成,包含智谱AI(chat_models.zhipuai)
    - blues_aka.config.config: 配置管理

使用示例:
    >>> from blues_aka.core.models import get_chat_model, get_model_by_preset
    >>> # 获取默认模型
    >>> model = get_chat_model()
    >>> # 获取流式模型
    >>> streaming_model = get_streaming_model(temperature=0.8)
    >>> # 使用预设配置
    >>> fast_model = get_model_by_preset("fast")
"""

import logging
from typing import Optional, Any, Dict

# 新的导入方式
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models.zhipuai import ChatZhipuAI
from blues_aka.config.config import ConfigFactory
from blues_aka.core.chat_models import ChatZhipuAIWithThinking

logger = logging.getLogger(__name__)

# 获取配置实例
_config = ConfigFactory.get_config()

# 获取聊天模型
def get_chat_model(
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = None,
        thinking_type: Optional[str] = None,
        **kwargs: Any
) -> BaseChatModel:
    """
    获取配置好的聊天模型实例

    该函数创建并返回一个智谱AI聊天模型实例,使用配置文件中的默认值或传入的参数进行配置。
    支持自定义模型名称、温度、最大token数和流式输出等参数。

    Args:
        model_name: 模型名称,如 'glm-4.5', 'glm-4.6' 等。默认使用配置文件中的模型
        temperature: 温度参数,控制输出的随机性(0.0-1.0)。默认使用配置文件中的值
        max_tokens: 最大生成token数。默认使用配置文件中的值
        streaming: 是否启用流式输出。默认使用配置文件中的值
        **kwargs: 其他传递给ChatZhipuAI的参数

    Returns:
        BaseChatModel: 配置好的聊天模型实例

    Raises:
        Exception: 当模型创建失败时抛出异常

    Example:
        >>> # 使用默认配置
        >>> model = get_chat_model()
        >>> # 自定义参数
        >>> model = get_chat_model(
        ...     model_name="glm-4.6",
        ...     temperature=0.8,
        ...     max_tokens=2000,
        ...     streaming=True
        ... )
        >>> # 传递额外参数
        >>> model = get_chat_model(top_p=0.9)

    Note:
        - 所有参数都有默认值,会从配置文件中读取
        - 如果模型创建失败,会记录错误日志并重新抛出异常
        - 传入的kwargs参数会覆盖默认配置
    """
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

    if thinking_type is not None:
        # 智谱AI深度思考配置
        # 注意：只有部分模型支持深度思考功能，如 glm-4-plus
        if thinking_type == "enabled":
            model_config['thinking'] = {
                "type": "enabled"  # 或者使用 "auto"
            }
            logger.info(f"模型 {model_name} 深度思考模式: {thinking_type}")
        elif thinking_type == "auto":
            model_config['thinking'] = {
                "type": "auto"
            }
            logger.info(f"模型 {model_name} 深度思考模式: auto")
        else:
            model_config['thinking'] = {"type": thinking_type}
            logger.info(f"模型 {model_name} 深度思考模式: {thinking_type}")

    model_config.update(kwargs)
    logger.info(model_config)

    try:
        model = ChatZhipuAIWithThinking(**model_config)
        return model
    except Exception as e:
        logger.error(f"模型创建失败: {e}")
        raise

def get_streaming_model(
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
) -> BaseChatModel:
    """
    获取流式输出的聊天模型

    该函数是get_chat_model的便捷封装,自动将streaming参数设置为True。
    流式输出适合实时响应场景,可以在生成过程中逐步返回结果。

    Args:
        model_name: 模型名称。默认使用配置文件中的模型
        temperature: 温度参数。默认使用配置文件中的值
        **kwargs: 其他传递给ChatZhipuAI的参数

    Returns:
        BaseChatModel: 配置好流式输出的聊天模型实例

    Example:
        >>> model = get_streaming_model(temperature=0.8)
        >>> for chunk in model.stream("你好"):
        ...     print(chunk.content, end="")

    Note:
        - streaming参数固定为True
        - 适合需要实时展示生成结果的场景
        - 可以通过模型的stream方法逐步获取生成内容
    """
    return get_chat_model(model_name=model_name, temperature=temperature, streaming=True, **kwargs)

def get_thinking_model(
    model_name: Optional[str] = None,
    **kwargs: Any
) -> BaseChatModel:
    """
    获取启用深度思考的模型（便捷方法）

    Args:
        model_name: 模型名称
        **kwargs: 其他参数

    Returns:
        BaseChatModel: 启用深度思考的模型实例

    Example:
        >>> model = get_thinking_model(model_name="glm-4.7")
        >>> for chunk in model.stream("分析一下量子计算的原理"):
        ...     print(chunk.content, end="")
    """
    return get_chat_model(
        model_name=model_name,
        thinking_type="enabled",
        **kwargs
    )

def getStructuredOutputModel(
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any
) -> BaseChatModel:
    """
    获取结构化输出的聊天模型

    该函数是get_chat_model的便捷封装,专门用于需要结构化输出的场景。
    默认温度设置为0.0以确保输出的一致性和可预测性。

    Args:
        model_name: 模型名称。默认使用配置文件中的模型
        temperature: 温度参数,默认为0.0以确保输出稳定
        **kwargs: 其他传递给ChatZhipuAI的参数

    Returns:
        BaseChatModel: 配置好的聊天模型实例,禁用流式输出

    Example:
        >>> model = getStructuredOutputModel()
        >>> response = model.invoke("请以JSON格式回复")

    Note:
        - streaming参数固定为False
        - temperature默认为0.0,适合需要精确输出的场景
        - 适合需要特定格式输出的任务,如JSON、XML等
    """
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
"""
预定义的模型配置字典

该字典定义了常用的模型预设配置,每个预设包含:
- model_name: 智谱AI模型名称
- temperature: 温度参数
- description: 预设描述

可用预设:
    - default: glm-4.5, 温度0.7, 平衡性能和成本
    - fast: glm-4.5-air, 温度0.7, 快速响应
    - precise: glm-4.6, 温度0.3, 高准确性
    - creative: glm-4.6, 温度1.0, 高创造性
    - multimodal: glm-4.5V, 温度0.7, 支持多模态输入
"""

def get_model_by_preset(preset: str = "default", **kwargs: Any) -> BaseChatModel:
    """
    根据预设配置获取模型

    该函数根据预定义的配置名称快速获取配置好的模型实例。
    预设配置针对不同场景优化了模型参数。

    Args:
        preset: 预设配置名称,可选值为:
            - 'default': 默认模型,平衡性能和成本
            - 'fast': 快速模型,适合简单任务
            - 'precise': 精确模型,适合需要准确性的任务
            - 'creative': 创意模型,适合需要创造性的任务
            - 'multimodal': 多模态模型,支持图片输入
        **kwargs: 额外的配置参数,会覆盖预设配置

    Returns:
        BaseChatModel: 根据预设配置好的聊天模型实例

    Raises:
        ValueError: 当传入未知的预设名称时抛出异常

    Example:
        >>> # 使用默认预设
        >>> model = get_model_by_preset()
        >>> # 使用快速预设
        >>> model = get_model_by_preset("fast")
        >>> # 覆盖预设的temperature参数
        >>> model = get_model_by_preset("precise", temperature=0.5)

    Note:
        - 预设配置针对特定场景进行了优化
        - 可以通过kwargs覆盖预设中的任何参数
        - description字段不会传递给模型
    """
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
    """
    获取模型信息字符串

    该函数生成一个包含提供商和模型名称的字符串,用于日志记录或显示模型信息。

    Args:
        model_name: 模型名称。默认使用配置文件中的模型
        provider: 模型提供商名称,默认为"ZhiPuAI"

    Returns:
        str: 格式为 "提供商 : 模型名称" 的字符串

    Example:
        >>> get_model_string()
        'ZhiPuAI : glm-4.5'
        >>> get_model_string("glm-4.6", "ZhiPuAI")
        'ZhiPuAI : glm-4.6'

    Note:
        - 会自动记录模型信息到日志
        - 主要用于调试和日志记录
    """
    model_name = model_name or _config.default_model
    model_string = f"{provider} : {model_name}"
    logger.info(model_string)
    return model_string
