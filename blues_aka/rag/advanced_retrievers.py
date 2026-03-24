"""高级 RAG 检索器模块

该模块提供了高级检索功能，包括:
- 重排序（Reranking）
- 查询扩展（Query Expansion）
- 混合检索（Hybrid Search）
- BM25 + 语义检索

主要功能:
    - RerankingRetriever: 带 CrossEncoder 重排序的检索器
    - QueryExpansionRetriever: 查询扩展检索器
    - HybridRetriever: BM25 + 向量混合检索
    - AdvancedRAGRetriever: 集成所有高级功能的检索器

Author: Blues AKA Team
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class RerankingRetriever(BaseRetriever):
    """
    带重排序功能的检索器

    使用 CrossEncoder 对检索结果进行重排序，提高检索准确性。

    主要特性:
        1. 先使用基础检索器获取候选文档
        2. 使用 CrossEncoder 对候选文档重新打分
        3. 返回重排序后的 top-k 结果

    使用示例:
        >>> from blues_aka.rag.advanced_retrievers import RerankingRetriever
        >>>
        >>> base_retriever = create_retriever(vector_store)
        >>> reranking_retriever = RerankingRetriever(
        ...     base_retriever=base_retriever,
        ...     top_k=20,  # 获取20个候选
        ...     rerank_top_k=5  # 返回重排序后的top 5
        ... )
        >>>
        >>> docs = reranking_retriever.invoke("什么是机器学习？")
    """

    def __init__(
        self,
        base_retriever: BaseRetriever,
        top_k: int = 20,
        rerank_top_k: int = 5,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_reranker: bool = True
    ):
        """
        初始化 RerankingRetriever

        Args:
            base_retriever: 基础检索器，用于获取候选文档
            top_k: 从基础检索器获取的候选文档数量
                - 获取更多候选可以提高重排序效果
                - 默认 20
            rerank_top_k: 重排序后返回的文档数量
                - 通常小于 top_k
                - 默认 5
            model_name: CrossEncoder 模型名称
                - 默认使用轻量级模型
                - 可选: "cross-encoder/ms-marco-MiniLM-L-6-v2"
                - 可选: "cross-encoder/ms-marco-MiniLM-L-12-v2"
            use_reranker: 是否使用重排序
                - True: 使用 CrossEncoder 重排序
                - False: 直接返回基础检索器结果
                - 默认 True
        """
        self.base_retriever = base_retriever
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k
        self.model_name = model_name
        self.use_reranker = use_reranker
        self.reranker = None

        # 延迟加载 reranker（避免导入时的性能开销）
        if use_reranker:
            try:
                from sentence_transformers import CrossEncoder
                self.reranker = CrossEncoder(model_name)
                logger.info(f"CrossEncoder 加载成功: {model_name}")
            except ImportError:
                logger.warning("sentence_transformers 未安装，重排序功能将被禁用")
                logger.warning("安装命令: pip install sentence-transformers")
                self.use_reranker = False
            except Exception as e:
                logger.warning(f"CrossEncoder 加载失败: {e}，重排序功能将被禁用")
                self.use_reranker = False

    def _get_relevant_documents(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Document]:
        """
        检索并重排序文档

        Args:
            query: 查询文本
            **kwargs: 其他参数

        Returns:
            List[Document]: 重排序后的文档列表
        """
        # 第一步: 使用基础检索器获取候选文档
        logger.debug(f"获取候选文档: top_k={self.top_k}")
        candidates = self.base_retriever.invoke(query, **kwargs)

        # 如果候选文档少于 rerank_top_k，直接返回
        if len(candidates) <= self.rerank_top_k:
            logger.debug(f"候选文档数量 ({len(candidates)}) <= rerank_top_k，直接返回")
            return candidates

        # 如果不使用重排序，直接返回前 rerank_top_k 个
        if not self.use_reranker or self.reranker is None:
            logger.debug("重排序未启用，返回基础检索器结果")
            return candidates[:self.rerank_top_k]

        # 第二步: 使用 CrossEncoder 重排序
        try:
            logger.debug(f"开始重排序 {len(candidates)} 个候选文档")

            # 构建查询-文档对
            pairs = [[query, doc.page_content] for doc in candidates]

            # 计算相似度分数
            scores = self.reranker.predict(pairs)

            # 按分数排序
            scored_docs = list(zip(candidates, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            # 返回 top-k
            reranked_docs = [doc for doc, score in scored_docs[:self.rerank_top_k]]

            logger.debug(f"重排序完成，返回 top {len(reranked_docs)} 个文档")
            logger.debug(f"重排序分数: {[f'{score:.4f}' for _, score in scored_docs[:self.rerank_top_k]]}")

            return reranked_docs

        except Exception as e:
            logger.error(f"重排序失败: {e}，返回基础检索器结果")
            return candidates[:self.rerank_top_k]


class QueryExpansionRetriever(BaseRetriever):
    """
    查询扩展检索器

    使用 LLM 生成多个查询变体，提高召回率。

    主要特性:
        1. 使用 LLM 生成多个查询变体
        2. 对每个查询进行检索
        3. 合并去重结果

    使用示例:
        >>> from blues_aka.rag.advanced_retrievers import QueryExpansionRetriever
        >>>
        >>> base_retriever = create_retriever(vector_store)
        >>> expansion_retriever = QueryExpansionRetriever(
        ...     base_retriever=base_retriever,
        ...     model=model,
        ...     num_queries=3,
        ...     top_k_per_query=3
        ... )
        >>>
        >>> docs = expansion_retriever.invoke("深度学习的应用")
    """

    def __init__(
        self,
        base_retriever: BaseRetriever,
        model: BaseChatModel,
        num_queries: int = 3,
        top_k_per_query: int = 3,
        final_top_k: int = 10
    ):
        """
        初始化 QueryExpansionRetriever

        Args:
            base_retriever: 基础检索器
            model: 语言模型，用于生成查询扩展
            num_queries: 生成的查询变体数量
                - 不包括原始查询
                - 默认 3
            top_k_per_query: 每个查询返回的文档数量
                - 默认 3
            final_top_k: 最终返回的文档数量
                - 默认 10
        """
        self.base_retriever = base_retriever
        self.model = model
        self.num_queries = num_queries
        self.top_k_per_query = top_k_per_query
        self.final_top_k = final_top_k

    def _expand_query(self, query: str) -> List[str]:
        """
        使用 LLM 生成查询扩展

        Args:
            query: 原始查询

        Returns:
            List[str]: 扩展后的查询列表（包括原始查询）
        """
        try:
            expansion_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个查询扩展助手。基于原始查询，生成多个不同角度的查询变体。

规则:
1. 生成 {num_queries} 个不同的查询变体
2. 每个查询应该从不同角度或使用不同的表达方式
3. 保持原始查询的核心意图
4. 只返回查询列表，每行一个，不要有编号或其他格式

示例:
原始查询: 深度学习的应用
扩展查询:
神经网络在计算机视觉中的应用
人工智能深度学习技术实际运用案例
DL深度学习框架应用实践"""),
                ("user", "原始查询: {query}\n\n扩展查询:")
            ])

            chain = expansion_prompt | self.model
            result = chain.invoke({"num_queries": self.num_queries, "query": query})

            # 解析结果
            expanded_text = result.content if hasattr(result, 'content') else str(result)
            expanded_queries = [
                line.strip()
                for line in expanded_text.strip().split('\n')
                if line.strip()
            ]

            # 确保包含原始查询
            expanded_queries.append(query)

            logger.debug(f"查询扩展: {query} -> {expanded_queries}")
            return expanded_queries

        except Exception as e:
            logger.warning(f"查询扩展失败: {e}，使用原始查询")
            return [query]

    def _get_relevant_documents(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Document]:
        """
        使用查询扩展进行检索

        Args:
            query: 原始查询
            **kwargs: 其他参数

        Returns:
            List[Document]: 检索到的文档列表（去重后）
        """
        # 第一步: 查询扩展
        expanded_queries = self._expand_query(query)
        logger.info(f"查询扩展完成: {len(expanded_queries)} 个查询")

        # 第二步: 对每个查询进行检索
        all_docs = []
        for i, expanded_query in enumerate(expanded_queries):
            try:
                docs = self.base_retriever.invoke(
                    expanded_query,
                    **kwargs
                )
                all_docs.extend(docs)
                logger.debug(f"查询 {i+1}/{len(expanded_queries)}: {expanded_query} -> {len(docs)} 个文档")
            except Exception as e:
                logger.warning(f"查询 '{expanded_query}' 检索失败: {e}")

        # 第三步: 去重
        unique_docs = self._deduplicate_documents(all_docs)

        # 第四步: 返回 top-k
        result = unique_docs[:self.final_top_k]
        logger.info(f"查询扩展检索完成: {len(all_docs)} 个候选 -> {len(unique_docs)} 个去重 -> {len(result)} 个返回")

        return result

    def _deduplicate_documents(self, docs: List[Document]) -> List[Document]:
        """
        去重文档（基于内容哈希）

        Args:
            docs: 文档列表

        Returns:
            List[Document]: 去重后的文档列表
        """
        seen = set()
        unique_docs = []

        for doc in docs:
            # 使用内容哈希去重
            content_hash = hashlib.md5(doc.page_content.encode()).hexdigest()

            if content_hash not in seen:
                seen.add(content_hash)
                unique_docs.append(doc)

        return unique_docs


class HybridRetriever(BaseRetriever):
    """
    混合检索器

    结合 BM25 关键词检索和向量语义检索，提高检索准确率。

    主要特性:
        1. BM25 检索: 精确匹配关键词
        2. 向量检索: 语义相似度匹配
        3. 加权融合: 平衡两种检索结果

    使用示例:
        >>> from blues_aka.rag.advanced_retrievers import HybridRetriever
        >>>
        >>> hybrid_retriever = HybridRetriever(
        ...     vector_store=vector_store,
        ...     documents=documents,
        ...     bm25_weight=0.3,
        ...     vector_weight=0.7,
        ...     top_k=5
        ... )
        >>>
        >>> docs = hybrid_retriever.invoke("机器学习算法")
    """

    def __init__(
        self,
        vector_store,
        documents: List[Document],
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        top_k: int = 5
    ):
        """
        初始化 HybridRetriever

        Args:
            vector_store: 向量存储实例
            documents: 文档列表（用于 BM25）
            bm25_weight: BM25 检索的权重
                - 默认 0.3
            vector_weight: 向量检索的权重
                - 默认 0.7
            top_k: 返回的文档数量
                - 默认 5

        注意:
            bm25_weight + vector_weight 应该等于 1.0
        """
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.top_k = top_k

        # 创建向量检索器
        self.vector_retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k * 2}  # 获取更多候选
        )

        # 创建 BM25 检索器
        try:
            from langchain_community.retrievers import BM25Retriever
            self.bm25_retriever = BM25Retriever.from_documents(
                documents,
                k=top_k * 2
            )
            logger.info("BM25 检索器创建成功")
        except ImportError:
            logger.warning("langchain-community 未安装，BM25 检索将被禁用")
            logger.warning("安装命令: pip install langchain-community")
            self.bm25_retriever = None
            self.bm25_weight = 0.0

        # 创建 EnsembleRetriever
        if self.bm25_retriever:
            try:
                from langchain_classic.retrievers import EnsembleRetriever
                self.ensemble_retriever = EnsembleRetriever(
                    retrievers=[self.bm25_retriever, self.vector_retriever],
                    weights=[bm25_weight, vector_weight]
                )
                logger.info(f"混合检索器创建成功: BM25={bm25_weight}, Vector={vector_weight}")
            except Exception as e:
                logger.warning(f"EnsembleRetriever 创建失败: {e}，只使用向量检索")
                self.ensemble_retriever = None
        else:
            self.ensemble_retriever = None

    def _get_relevant_documents(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Document]:
        """
        使用混合检索进行检索

        Args:
            query: 查询文本
            **kwargs: 其他参数

        Returns:
            List[Document]: 检索到的文档列表
        """
        if self.ensemble_retriever:
            # 使用混合检索
            docs = self.ensemble_retriever.invoke(query, **kwargs)
            logger.debug(f"混合检索: {len(docs)} 个文档")
            return docs[:self.top_k]
        else:
            # 只使用向量检索
            docs = self.vector_retriever.invoke(query, **kwargs)
            logger.debug(f"向量检索: {len(docs)} 个文档")
            return docs[:self.top_k]


class AdvancedRAGRetriever:
    """
    高级 RAG 检索器

    集成所有高级功能的检索器，包括:
    - 混合检索（BM25 + 向量）
    - 查询扩展
    - 重排序

    使用示例:
        >>> from blues_aka.rag.advanced_retrievers import AdvancedRAGRetriever
        >>>
        >>> advanced_retriever = AdvancedRAGRetriever(
        ...     vector_store=vector_store,
        ...     documents=documents,
        ...     model=model,
        ...     enable_reranking=True,
        ...     enable_query_expansion=True,
        ...     enable_hybrid_search=True
        ... )
        >>>
        >>> docs = advanced_retriever.retrieve("什么是深度学习？")
    """

    def __init__(
        self,
        vector_store,
        documents: List[Document],
        model: BaseChatModel,
        enable_reranking: bool = True,
        enable_query_expansion: bool = True,
        enable_hybrid_search: bool = True,
        **kwargs
    ):
        """
        初始化 AdvancedRAGRetriever

        Args:
            vector_store: 向量存储实例
            documents: 文档列表
            model: 语言模型（用于查询扩展）
            enable_reranking: 是否启用重排序
            enable_query_expansion: 是否启用查询扩展
            enable_hybrid_search: 是否启用混合检索
            **kwargs: 其他参数
        """
        self.vector_store = vector_store
        self.documents = documents
        self.model = model
        self.enable_reranking = enable_reranking
        self.enable_query_expansion = enable_query_expansion
        self.enable_hybrid_search = enable_hybrid_search

        # 构建检索器链
        self.retriever = self._build_retriever_chain(**kwargs)

        logger.info("AdvancedRAGRetriever 初始化完成")
        logger.info(f"重排序: {enable_reranking}")
        logger.info(f"查询扩展: {enable_query_expansion}")
        logger.info(f"混合检索: {enable_hybrid_search}")

    def _build_retriever_chain(self, **kwargs) -> BaseRetriever:
        """构建检索器链"""
        from blues_aka.rag.retrievers import create_retriever

        # 第一步: 基础检索器
        if self.enable_hybrid_search and self.documents:
            # 使用混合检索
            base_retriever = HybridRetriever(
                vector_store=self.vector_store,
                documents=self.documents,
                **kwargs
            )
        else:
            # 使用向量检索
            base_retriever = create_retriever(
                self.vector_store,
                **kwargs
            )

        # 第二步: 查询扩展
        if self.enable_query_expansion:
            retriever = QueryExpansionRetriever(
                base_retriever=base_retriever,
                model=self.model,
                **kwargs
            )
        else:
            retriever = base_retriever

        # 第三步: 重排序
        if self.enable_reranking:
            retriever = RerankingRetriever(
                base_retriever=retriever,
                **kwargs
            )

        return retriever

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        执行高级检索

        Args:
            query: 查询文本
            **kwargs: 其他参数

        Returns:
            List[Document]: 检索到的文档列表
        """
        return self.retriever.invoke(query, **kwargs)

    def get_retriever(self) -> BaseRetriever:
        """获取检索器实例"""
        return self.retriever
