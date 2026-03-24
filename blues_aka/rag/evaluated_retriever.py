"""带评估功能的检索器包装器

该模块提供了集成 RAG 评估功能的检索器包装器，
可以在检索过程中自动记录评估指标。

主要功能:
    - EvaluatedRetriever: 带评估的检索器包装器
    - 自动记录检索查询和结果
    - 追踪 token 使用量
    - 记录检索性能指标

使用示例:
    >>> from blues_aka.rag.evaluated_retriever import create_evaluated_retriever
    >>> retriever = create_evaluated_retriever(base_retriever)
    >>> docs = retriever.invoke("查询问题")  # 自动记录指标
"""
import logging
from typing import Any, List

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from blues_aka.rag.evaluator import get_rag_metrics_tracker

logger = logging.getLogger(__name__)


class EvaluatedRetriever(BaseRetriever):
    """带评估功能的检索器包装器

    在执行检索的同时记录评估指标，包括：
    - 查询次数
    - 检索文档数量
    - Token 使用量（估算）
    """

    base_retriever: BaseRetriever = None
    """基础检索器实例"""

    track_tokens: bool = True
    """是否追踪 token 使用量"""

    def __init__(
        self,
        base_retriever: BaseRetriever,
        track_tokens: bool = True,
    ):
        """
        初始化带评估的检索器

        Args:
            base_retriever: 基础检索器
            track_tokens: 是否追踪 token 使用量
        """
        super().__init__()
        self.base_retriever = base_retriever
        self.track_tokens = track_tokens

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any,
    ) -> List[Document]:
        """
        执行检索并记录指标

        Args:
            query: 查询文本
            run_manager: 运行管理器
            **kwargs: 额外参数

        Returns:
            检索到的文档列表
        """
        logger.debug(f"[EvaluatedRetriever] 开始检索: {query[:50]}...")
        logger.debug(f"[EvaluatedRetriever] 基础检索器类型: {type(self.base_retriever).__name__}")

        # 执行基础检索 - 兼容不同的检索器实现
        # 优先使用 invoke() 方法（LangChain 标准），回退到 get_relevant_documents()
        docs = None
        error_msgs = []

        # 尝试 1: 使用 invoke() 方法（新版本 LangChain）
        if hasattr(self.base_retriever, 'invoke'):
            try:
                logger.debug(f"[EvaluatedRetriever] 尝试使用 invoke() 方法")
                result = self.base_retriever.invoke(query, **kwargs)
                # invoke() 返回的是 RetrieverResult，需要提取文档
                if hasattr(result, 'documents'):
                    docs = result.documents
                    logger.debug(f"[EvaluatedRetriever] invoke() 返回 RetrieverResult，提取文档")
                else:
                    docs = result
                    logger.debug(f"[EvaluatedRetriever] invoke() 直接返回文档列表")
                logger.info(f"[EvaluatedRetriever] ✅ 使用 invoke() 成功检索到 {len(docs) if docs else 0} 个文档")
            except Exception as e:
                error_msgs.append(f"invoke() 失败: {e}")
                logger.warning(f"[EvaluatedRetriever] invoke() 调用失败: {e}")

        # 尝试 2: 使用 get_relevant_documents() 方法（旧版本或兼容层）
        if docs is None and hasattr(self.base_retriever, 'get_relevant_documents'):
            try:
                logger.debug(f"[EvaluatedRetriever] 尝试使用 get_relevant_documents() 方法")
                docs = self.base_retriever.get_relevant_documents(query, **kwargs)
                logger.info(f"[EvaluatedRetriever] ✅ 使用 get_relevant_documents() 成功检索到 {len(docs) if docs else 0} 个文档")
            except Exception as e:
                error_msgs.append(f"get_relevant_documents() 失败: {e}")
                logger.warning(f"[EvaluatedRetriever] get_relevant_documents() 调用失败: {e}")

        # 尝试 3: 尝试作为可调用对象
        if docs is None and callable(self.base_retriever):
            try:
                logger.debug(f"[EvaluatedRetriever] 尝试作为可调用对象")
                docs = self.base_retriever(query, **kwargs)
                logger.info(f"[EvaluatedRetriever] ✅ 使用可调用方式成功检索到 {len(docs) if docs else 0} 个文档")
            except Exception as e:
                error_msgs.append(f"可调用方式失败: {e}")
                logger.warning(f"[EvaluatedRetriever] 可调用方式失败: {e}")

        # 如果所有方法都失败，抛出异常
        if docs is None:
            error_msg = f"[EvaluatedRetriever] ❌ 所有检索方法都失败: {'; '.join(error_msgs)}"
            logger.error(error_msg)
            raise AttributeError(error_msg)

        # 确保 docs 是列表
        if not isinstance(docs, list):
            docs = list(docs)

        # 估算 token 使用量（中文约 1.5 字符/token）
        query_tokens = len(query) // 2 + 10  # 粗略估计
        doc_tokens = sum(len(doc.page_content) // 2 for doc in docs) if docs else 0
        total_tokens = query_tokens + doc_tokens

        # 记录查询指标
        try:
            metrics_tracker = get_rag_metrics_tracker()
            metrics_tracker.record_query(
                query=query,
                retrieved_count=len(docs),
                tokens_used=total_tokens if self.track_tokens else 0
            )
            logger.debug(
                f"[EvaluatedRetriever] 已记录指标 - "
                f"检索 {len(docs)} 个文档, 约 {total_tokens} tokens"
            )
        except Exception as e:
            logger.warning(f"记录检索指标失败: {e}")

        return docs

    @property
    def _llm_type(self) -> str:
        """返回检索器类型标识"""
        return f"evaluated_{self.base_retriever.__class__.__name__}"


def create_evaluated_retriever(
    base_retriever: BaseRetriever,
    track_tokens: bool = True,
) -> EvaluatedRetriever:
    """
    创建带评估功能的检索器

    这是一个便捷函数，用于包装现有的检索器以添加评估功能。

    Args:
        base_retriever: 基础检索器
        track_tokens: 是否追踪 token 使用量

    Returns:
        带评估功能的检索器

    Example:
        >>> from blues_aka.rag.retrievers import create_retriever
        >>> from blues_aka.rag.evaluated_retriever import create_evaluated_retriever
        >>>
        >>> # 创建基础检索器
        >>> base_retriever = create_retriever(vector_store)
        >>>
        >>> # 包装为带评估的检索器
        >>> evaluated_retriever = create_evaluated_retriever(base_retriever)
        >>>
        >>> # 使用检索器（自动记录指标）
        >>> docs = evaluated_retriever.invoke("查询问题")
    """
    logger.info("创建带评估功能的检索器")
    return EvaluatedRetriever(
        base_retriever=base_retriever,
        track_tokens=track_tokens
    )
