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

# 向量库类型
VectorStoreType = Literal["faiss", "inmemory"]

def create_vector_store(
    documents: List[Document],
    embeddings: Embeddings,
    store_type: Optional[VectorStoreType] = None,
    **kwargs,
) -> VectorStore:
    """从文档创建向量存储"""
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
    """保存向量存储到磁盘"""
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
    """从磁盘加载向量存储"""
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
    """向现有向量库添加文档"""
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
    """在向量库中搜索相似文档"""
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
    """获取向量库的统计信息"""
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
    """删除向量库文件"""
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