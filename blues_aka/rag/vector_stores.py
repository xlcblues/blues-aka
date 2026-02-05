"""向量存储管理模块

该模块提供了向量存储的创建、保存、加载、搜索和删除功能。
支持 FAISS 和 InMemory 两种向量存储类型，用于高效的文档向量检索。

主要功能:
    - create_vector_store: 从文档创建向量存储
    - save_vector_store: 保存向量存储到磁盘
    - load_vector_store: 从磁盘加载向量存储
    - add_documents_to_vector_store: 向现有向量存储添加文档
    - search_vector_store: 在向量存储中搜索相似文档
    - get_vector_store_stats: 获取向量存储的统计信息
    - delete_vector_store: 删除向量存储文件

支持的向量库类型:
    - faiss: Facebook AI Similarity Search，高性能向量索引库
    - inmemory: 内存向量存储，适合测试和小规模数据

Example:
    >>> from blues_aka.rag.vector_stores import create_vector_store, save_vector_store
    >>> from blues_aka.rag.embeddings import get_embeddings
    >>>
    >>> embeddings = get_embeddings()
    >>> vector_store = create_vector_store(documents, embeddings, store_type="faiss")
    >>> save_vector_store(vector_store, "./my_index", embeddings)
"""
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Literal

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore, InMemoryVectorStore

try:
    from langchain_community.vectorstores import FAISS
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

logger = logging.getLogger(__name__)

# 向量库类型字面量类型
VectorStoreType = Literal["faiss", "inmemory"]

def create_vector_store(
    documents: List[Document],
    embeddings: Embeddings,
    store_type: Optional[VectorStoreType] = None,
    **kwargs,
) -> VectorStore:
    """从文档创建向量存储

    使用文档列表和嵌入模型创建一个新的向量存储实例。

    Args:
        documents (List[Document]): 要添加到向量存储的文档列表
        embeddings (Embeddings): 用于生成文档向量的嵌入模型
        store_type (Optional[VectorStoreType]): 向量存储类型，支持:
            - "faiss": FAISS 向量存储（推荐，支持持久化）
            - "inmemory": 内存向量存储（仅用于测试）
            如果为 None 则使用配置文件中的默认值
            默认值: None
        **kwargs: 传递给具体向量存储类的其他参数

    Returns:
        VectorStore: 创建的向量存储实例

    Raises:
        ValueError: 当文档列表为空或不支持的向量库类型时抛出异常
        ImportError: 当使用 FAISS 但未安装时抛出异常
        Exception: 创建向量存储失败时抛出异常

    Note:
        - FAISS 需要单独安装: pip install faiss-cpu
        - InMemoryVectorStore 仅用于测试，不支持持久化
        - 创建的向量存储可以用于相似度搜索和检索

    Example:
        >>> from blues_aka.rag.embeddings import get_embeddings
        >>> embeddings = get_embeddings()
        >>> vector_store = create_vector_store(
        >>>     documents,
        >>>     embeddings,
        >>>     store_type="faiss"
        >>> )
        >>> results = vector_store.similarity_search("查询问题")
    """
    from blues_aka import ConfigFactory
    _config = ConfigFactory.get_config()

    if documents is None:
        raise ValueError("文档列表不能为空")
    store_type = store_type or _config.vector_store_type
    logger.info(f"创建向量存储: type={store_type}, documents={len(documents)}")

    try:
        if store_type == "faiss":
            if not FAISS_AVAILABLE:
                raise ImportError("FAISS 未安装。请运行: pip install faiss-cpu")

            # FAISS.from_documents 期望的参数名是 embedding (单数)
            vector_store = FAISS.from_documents(
                documents=documents,
                embedding=embeddings,
                **kwargs
            )
            logger.info("FAISS 向量库创建成功")
        elif store_type == "inmemory":
            vector_store = InMemoryVectorStore.from_documents(
                documents=documents,
                embedding=embeddings,
                **kwargs
            )
            logger.info("inmemory 向量库创建成功")
        else:
            raise ValueError(
                f"不支持的向量库类型: {store_type}。"
                f"支持的类型: faiss, inmemory"
            )
        return vector_store

    except Exception as e:
        logger.error(f"创建向量库失败: {e}")
        raise

def save_vector_store(
    vector_store: VectorStore,
    save_path: str,
    embeddings: Optional[Embeddings] = None,
) -> None:
    """保存向量存储到磁盘

    将向量存储持久化到指定路径，以便后续加载使用。

    Args:
        vector_store (VectorStore): 要保存的向量存储实例
        save_path (str): 保存路径（目录或文件路径）
        embeddings (Optional[Embeddings]): 嵌入模型（某些向量库类型需要）
            默认值: None

    Raises:
        ValueError: 当向量存储类型不支持持久化时抛出异常
        Exception: 保存向量存储失败时抛出异常

    Note:
        - FAISS 支持持久化，会保存索引文件到指定目录
        - InMemoryVectorStore 不支持持久化
        - 如果父目录不存在，会自动创建
        - 保存后可以通过 load_vector_store 加载

    Example:
        >>> vector_store = create_vector_store(documents, embeddings)
        >>> save_vector_store(vector_store, "./my_index", embeddings)
        >>> # 稍后加载
        >>> loaded = load_vector_store("./my_index", embeddings)
    """
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"保存向量库: {save_path}")

    try:
        if isinstance(vector_store, FAISS):
            vector_store.save_local(str(save_path))
            logger.info("FAISS 向量库保存成功")
        elif isinstance(vector_store, InMemoryVectorStore):
            logger.warning("InMemoryVectorStore 不支持持久化")
            raise ValueError("InMemoryVectorStore 不支持持久化")
        else:
            logger.warning(f"未知的向量库类型: {type(vector_store)}")
            raise ValueError(f"不支持的向量库类型: {type(vector_store)}")

    except Exception as e:
        logger.error(f"保存向量库失败: {e}")
        raise

def load_vector_store(
    load_path: str,
    embeddings: Embeddings,
    store_type: Optional[VectorStoreType] = None,
    **kwargs,
) -> VectorStore:
    """从磁盘加载向量存储

    从磁盘加载之前保存的向量存储实例。

    Args:
        load_path (str): 向量存储的保存路径
        embeddings (Embeddings): 用于加载向量存储的嵌入模型
        store_type (Optional[VectorStoreType]): 向量存储类型
            如果为 None 则使用配置文件中的默认值
            默认值: None
        **kwargs: 传递给具体向量存储类的其他参数

    Returns:
        VectorStore: 加载的向量存储实例

    Raises:
        FileNotFoundError: 当向量存储路径不存在时抛出异常
        ImportError: 当使用 FAISS 但未安装时抛出异常
        ValueError: 当向量存储类型不支持从磁盘加载时抛出异常
        Exception: 加载向量存储失败时抛出异常

    Note:
        - FAISS 支持从磁盘加载
        - InMemoryVectorStore 不支持从磁盘加载
        - 加载时使用 allow_dangerous_deserialization=True 以允许加载 pickle 文件

    Example:
        >>> embeddings = get_embeddings()
        >>> vector_store = load_vector_store("./my_index", embeddings)
        >>> results = vector_store.similarity_search("查询问题")
    """
    from blues_aka import ConfigFactory
    _config = ConfigFactory.get_config()

    load_path = Path(load_path)

    if not load_path.exists():
        raise FileNotFoundError(f"向量库路径不存在: {load_path}")

    store_type = store_type or _config.vector_store_type
    logger.info(f"加载向量库: {load_path}")

    try:
        if store_type == "faiss":
            if not FAISS_AVAILABLE:
                raise ImportError("FAISS 未安装。请运行: pip install faiss-cpu")
            vector_store = FAISS.load_local(
                folder_path=str(load_path),
                embeddings=embeddings,
                allow_dangerous_deserialization=True,
                **kwargs
            )
            logger.info("FAISS 向量库加载成功")

        elif store_type == "inmemory":
            raise ValueError("InMemoryVectorStore 不支持从磁盘加载")

        else:
            raise ValueError(
                f"不支持的向量库类型: {store_type}。"
                f"支持的类型: faiss"
            )
        return vector_store

    except Exception as e:
        logger.error(f"加载向量库失败: {e}")
        raise

def add_documents_to_vector_store(
    vector_store: VectorStore,
    documents: List[Document],
) -> None:
    """向现有向量库添加文档

    将新的文档添加到已存在的向量存储中，自动生成向量并更新索引。

    Args:
        vector_store (VectorStore): 要添加文档的向量存储实例
        documents (List[Document]): 要添加的文档列表

    Raises:
        Exception: 添加文档失败时抛出异常

    Note:
        - 如果文档列表为空，函数会直接返回，不执行任何操作
        - 添加的文档会自动生成向量并添加到索引中
        - 添加后的文档可以立即被检索到

    Example:
        >>> vector_store = create_vector_store(initial_docs, embeddings)
        >>> new_docs = [Document(page_content="新的文档内容")]
        >>> add_documents_to_vector_store(vector_store, new_docs)
    """
    if not documents:
        logger.warning("文档列表为空，无需添加")
        return

    logger.info(f"向向量库添加文档: {len(documents)} 个")

    try:
        vector_store.add_documents(documents)
        logger.info("文档添加成功")

    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        raise

def search_vector_store(
    vector_store: VectorStore,
    query: str,
    k: int = 4,
    score_threshold: Optional[float] = None,
) -> List[tuple[Document, float]]:
    """在向量库中搜索相似文档

    根据查询文本在向量存储中搜索最相似的文档，返回文档及其相似度得分。

    Args:
        vector_store (VectorStore): 要搜索的向量存储实例
        query (str): 查询文本
        k (int): 返回的最相似文档数量
            默认值: 4
        score_threshold (Optional[float]): 相似度得分阈值，只返回得分高于此阈值的结果
            较低的得分表示更高的相似度（基于距离度量）
            如果为 None 则返回所有 k 个结果
            默认值: None

    Returns:
        List[tuple[Document, float]]: 包含文档和相似度得分的元组列表
            得分越低表示相似度越高

    Raises:
        Exception: 搜索失败时抛出异常

    Note:
        - 得分计算方式取决于向量存储类型（通常是欧氏距离或余弦距离）
        - 得分值越小表示文档与查询越相似
        - 使用 score_threshold 可以过滤掉相似度较低的结果

    Example:
        >>> vector_store = create_vector_store(documents, embeddings)
        >>> results = search_vector_store(
        >>>     vector_store,
        >>>     "如何使用 Python?",
        >>>     k=5,
        >>>     score_threshold=0.5
        >>> )
        >>> for doc, score in results:
        >>>     print(f"得分: {score:.4f}, 内容: {doc.page_content[:50]}...")
    """
    logger.info(f"搜索向量库: query='{query[:50]}...', k={k}")

    try:
        results = vector_store.similarity_search_with_score(
            query=query,
            k=k,
        )

        if score_threshold is not None:
            results = [(doc, score) for doc, score in results if score >= score_threshold]

        logger.info(f"找到 {len(results)} 个相关文档")
        return results

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise

def get_vector_store_stats(vector_store: VectorStore) -> dict:
    """获取向量库的统计信息

    获取向量存储的元数据和统计信息，用于监控和调试。

    Args:
        vector_store (VectorStore): 要获取统计信息的向量存储实例

    Returns:
        dict: 包含统计信息的字典，可能包含以下字段:
            - type (str): 向量存储类型名称
            - num_documents (int): 文档数量（FAISS）或 "N/A"（InMemory）
            - dimension (int): 向量维度（FAISS）

    Note:
        - 不同类型的向量存储返回的统计信息可能不同
        - FAISS 返回文档数量和向量维度
        - InMemoryVectorStore 仅返回类型信息
        - 如果获取统计信息失败，会记录警告但不中断程序

    Example:
        >>> vector_store = create_vector_store(documents, embeddings)
        >>> stats = get_vector_store_stats(vector_store)
        >>> print(f"文档数量: {stats['num_documents']}")
        >>> print(f"向量维度: {stats['dimension']}")
    """
    stats = {
        "type": type(vector_store).__name__,
    }

    try:
        if isinstance(vector_store, FAISS):
            stats["num_documents"] = vector_store.index.ntotal
            stats["dimension"] = vector_store.index.d

        elif isinstance(vector_store, InMemoryVectorStore):
            stats["num_documents"] = "N/A"

    except Exception as e:
        logger.warning(f"获取统计信息失败: {e}")

    logger.info("向量库统计:")
    for k, v in stats.items():
        logger.info(f"{k}: {v}")

    return stats

def delete_vector_store(path: str) -> None:
    """删除向量库文件

    从磁盘删除向量存储的文件或目录，释放存储空间。

    Args:
        path (str): 向量存储的路径（文件或目录）

    Raises:
        Exception: 删除向量存储失败时抛出异常

    Note:
        - 如果路径不存在，函数会记录警告并直接返回
        - 支持删除文件和目录
        - 删除目录时会递归删除所有内容
        - 删除操作不可逆，请谨慎使用

    Example:
        >>> save_vector_store(vector_store, "./temp_index", embeddings)
        >>> # 稍后不再需要时删除
        >>> delete_vector_store("./temp_index")
    """
    path = Path(path)

    if not path.exists():
        logger.warning(f"向量库不存在: {path}")
        return

    logger.info(f"删除向量库: {path}")

    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

        logger.info("向量库删除成功")

    except Exception as e:
        logger.error(f"删除向量库失败: {e}")
        raise