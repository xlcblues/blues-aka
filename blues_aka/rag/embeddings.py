import logging
from typing import Optional

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

from blues_aka import ConfigFactory

logger = logging.getLogger(__name__)
_config = ConfigFactory.get_config()

def get_embeddings(
    model: Optional[str] = None,
    batch_size: Optional[int] = None,
    **kwargs,
) -> Embeddings:
    """获取 Embedding 模型实例"""
    model = model or _config.embedding_model
    batch_size = batch_size or _config.embedding_batch_size

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
    """获取 Embedding 模型的向量维度"""
    model = model or _config.embedding_model
    dimensions = {
        "embedding-3": 1024,
    }

    if model not in dimensions:
        logger.warning(f"未知的模型维度: {model}，返回默认值 1024")
        return 1024

    return dimensions[model]

# 预定义的 Embedding 配置
EMBEDDING_CONFIGS = {
    "fast": {
        "model": "embedding-3",
        "description": "快速模型，适合开发和测试",
    }
}

def get_embeddings_by_preset(
    preset: str = "fast",
    **kwargs,
) -> Embeddings:
    """根据预设配置获取Embedding模型"""
    if preset not in EMBEDDING_CONFIGS:
        available = ", ".join(EMBEDDING_CONFIGS.keys())
        raise ValueError(f"未知的预设: {preset}. 可用预设: {available}")

    config = EMBEDDING_CONFIGS[preset].copy()
    model = config.pop("model")
    config.pop("description")
    config.update(kwargs)
    logger.info(f"使用预设 Embedding 配置: {preset}")
    return get_embeddings(model=model, **config)