"""Embedding 模型管理模块

该模块提供了创建和管理 Embedding 模型的功能，用于将文本转换为向量表示。
支持多种配置方式，包括自定义参数和预设配置。

主要功能:
    - get_embeddings: 创建自定义配置的 Embedding 模型
    - get_embedding_dimension: 获取模型的向量维度
    - get_embeddings_by_preset: 使用预设配置快速创建模型

Example:
    >>> from blues_aka.rag.embeddings import get_embeddings
    >>> embeddings = get_embeddings(model="embedding-3")
    >>> vectors = embeddings.embed_texts(["Hello world"])
"""
import logging
from typing import Optional

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


def get_embeddings(
    model: Optional[str] = None,
    batch_size: Optional[int] = None,
    **kwargs,
) -> Embeddings:
    """获取 Embedding 模型实例

    该函数用于创建一个 OpenAI 兼容的 Embedding 模型实例，用于将文本转换为向量表示。

    Args:
        model (Optional[str]): Embedding 模型名称，如果为 None 则使用配置文件中的默认模型。
            默认值: None (从配置文件读取)
        batch_size (Optional[int]): 批处理大小，控制每次请求处理的文本数量。
            如果为 None 则使用配置文件中的默认值。最大值为 64。
            默认值: None (从配置文件读取)
        **kwargs: 传递给 OpenAIEmbeddings 的其他参数

    Returns:
        Embeddings: LangChain Embeddings 实例，可用于生成文本向量

    Raises:
        Exception: 当创建 Embedding 模型失败时抛出异常

    Note:
        - 如果 batch_size 超过 API 限制（64），会自动调整为最大值
        - 使用 ConfigFactory 获取配置信息

    Example:
        >>> embeddings = get_embeddings(model="embedding-3", batch_size=32)
        >>> vectors = embeddings.embed_texts(["Hello", "World"])
    """
    from blues_aka import ConfigFactory
    _config = ConfigFactory.get_config()
    model = model or _config.embedding_model
    batch_size = batch_size or _config.embedding_batch_size

    # 确保 batch_size 不超过 API 限制
    max_batch_size = 64
    if batch_size > max_batch_size:
        logger.warning(f"batch_size {batch_size} 超过 API 限制 {max_batch_size}，已自动调整为 {max_batch_size}")
        batch_size = max_batch_size

    logger.info(f"创建 Embedding 模型: {model}")
    logger.debug(f"batch_size: {batch_size}")

    try:
        embeddings = OpenAIEmbeddings(
            model=model,
            api_key=_config.default_api_key,
            base_url=_config.default_api_base,
            chunk_size=batch_size,
            **kwargs
        )

        logger.debug(f"Embedding 模型创建成功")
        return embeddings

    except Exception as e:
        logger.error(f"创建 Embedding 模型失败: {e}")
        raise

def get_embedding_dimension(model: Optional[str] = None) -> int:
    """获取 Embedding 模型的向量维度

    根据模型名称返回对应的向量维度大小，用于创建向量数据库时的维度设置。

    Args:
        model (Optional[str]): Embedding 模型名称，如果为 None 则使用配置文件中的默认模型。
            默认值: None (从配置文件读取)

    Returns:
        int: 向量维度大小

    Note:
        - 目前支持的模型及其维度:
            - embedding-3: 1024
        - 如果传入未知模型，会记录警告日志并返回默认值 1024

    Example:
        >>> dim = get_embedding_dimension("embedding-3")
        >>> print(dim)  # 输出: 1024
    """
    model = model or _config.embedding_model
    dimensions = {
        "embedding-3": 1024,
    }

    if model not in dimensions:
        logger.warning(f"未知的模型维度: {model}，返回默认值 1024")
        return 1024

    return dimensions[model]


# 预定义的 Embedding 配置
EMBEDDING_CONFIGS: dict[str, dict[str, str]] = {
    "fast": {
        "model": "embedding-3",
        "description": "快速模型，适合开发和测试",
    }
}

def get_embeddings_by_preset(
    preset: str = "fast",
    **kwargs,
) -> Embeddings:
    """根据预设配置获取 Embedding 模型

    使用预定义的配置快速创建 Embedding 模型实例，避免重复配置相同参数。

    Args:
        preset (str): 预设配置名称，默认为 "fast"。
            可用预设:
                - "fast": 快速模型，适合开发和测试，使用 embedding-3 模型
            默认值: "fast"
        **kwargs: 额外的配置参数，会覆盖预设配置中的对应参数

    Returns:
        Embeddings: LangChain Embeddings 实例

    Raises:
        ValueError: 当传入未知的预设名称时抛出异常

    Example:
        >>> # 使用默认预设
        >>> embeddings = get_embeddings_by_preset()
        >>> # 使用指定预设
        >>> embeddings = get_embeddings_by_preset(preset="fast")
        >>> # 覆盖预设配置中的参数
        >>> embeddings = get_embeddings_by_preset(preset="fast", batch_size=16)
    """
    if preset not in EMBEDDING_CONFIGS:
        available = ", ".join(EMBEDDING_CONFIGS.keys())
        raise ValueError(f"未知的预设: {preset}. 可用预设: {available}")

    config = EMBEDDING_CONFIGS[preset].copy()
    model = config.pop("model")
    config.pop("description")
    config.update(kwargs)
    logger.info(f"使用预设 Embedding 配置: {preset}")
    return get_embeddings(model=model, **config)