"""向量检索器模块

该模块提供了创建和管理向量检索器的功能，支持多种检索策略和检索器组合。
可以用于构建 RAG（检索增强生成）系统的核心检索组件。

主要功能:
    - create_retriever: 从向量库创建基础检索器
    - create_retriever_tool: 将检索器封装为 LangChain Tool
    - create_multi_retriever: 创建组合多个检索器的集成检索器
    - get_retriever_config: 获取推荐的检索器配置

支持的检索类型:
    - similarity: 基本相似度检索
    - mmr: 最大边际相关性检索（结果更多样化）
    - similarity_score_threshold: 相似度阈值过滤（只返回高质量结果）

Example:
    >>> from blues_aka.rag.retrievers import create_retriever, create_retriever_tool
    >>> # 创建检索器
    >>> retriever = create_retriever(vector_store, search_type="mmr", k=5)
    >>> # 封装为工具
    >>> tool = create_retriever_tool(retriever, name="docs")
"""
import logging
from typing import Literal, Optional

from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_core.tools.retriever import create_retriever_tool as lc_create_retriever_tool
from langchain_classic.retrievers import EnsembleRetriever

logger = logging.getLogger(__name__)

# 检索类型字面量类型
SearchType = Literal["similarity", "mmr", "similarity_score_threshold"]

def create_retriever(
    vector_store: VectorStore,
    search_type: Optional[SearchType] = None,
    k: Optional[int] = None,
    score_threshold: Optional[float] = None,
    fetch_k: Optional[int] = None,
    **kwargs,
) -> BaseRetriever:
    """从向量库创建检索器

    从向量存储创建一个检索器实例，支持多种检索策略。

    Args:
        vector_store (VectorStore): 向量存储实例
        search_type (Optional[SearchType]): 检索类型，支持:
            - "similarity": 基本相似度检索（默认）
            - "mmr": 最大边际相关性检索
            - "similarity_score_threshold": 相似度阈值过滤
            如果为 None 则使用配置文件中的默认值
            默认值: None
        k (Optional[int]): 返回的文档数量
            如果为 None 则使用配置文件中的默认值
            默认值: None
        score_threshold (Optional[float]): 相似度阈值（仅用于 similarity_score_threshold）
            只返回相似度高于此阈值的文档
            如果为 None 则使用配置文件中的默认值
            默认值: None
        fetch_k (Optional[int]): MMR 检索时获取的文档数量（仅用于 mmr）
            从 fetch_k 个文档中选择 k 个最相关的
            如果为 None 则使用配置文件中的默认值
            默认值: None
        **kwargs: 传递给检索器的其他参数

    Returns:
        BaseRetriever: 创建的检索器实例

    Raises:
        Exception: 创建检索器失败时抛出异常

    Note:
        - similarity: 最快的检索方式，直接返回最相似的 k 个文档
        - mmr: 在相关性和多样性之间取得平衡，避免返回重复内容
        - similarity_score_threshold: 只返回相似度高于阈值的文档，提高结果质量

    Example:
        >>> # 基本相似度检索
        >>> retriever = create_retriever(vector_store, search_type="similarity", k=5)
        >>> # MMR 检索（更多样化）
        >>> retriever = create_retriever(vector_store, search_type="mmr", k=5, fetch_k=20)
        >>> # 阈值过滤（只返回高质量结果）
        >>> retriever = create_retriever(
        >>>     vector_store,
        >>>     search_type="similarity_score_threshold",
        >>>     score_threshold=0.7
        >>> )
        >>> docs = retriever.invoke("查询问题")
    """
    from blues_aka import ConfigFactory
    _config = ConfigFactory.get_config()

    search_type =search_type or _config.retriever_search_type
    k = k or _config.retriever_k
    score_threshold = score_threshold or _config.retriever_score_threshold
    fetch_k = fetch_k or _config.retriever_fetch_k
    logger.info(f"创建检索器: search_type={search_type}, k={k}")

    search_kwargs = {"k": k}

    if search_type == "mmr":
        search_kwargs["fetch_k"] = fetch_k
        logger.debug(f"MMR fetch_k: {fetch_k}")

    elif search_type == "similarity_score_threshold":
        search_kwargs["score_threshold"] = score_threshold
        logger.debug(f"相似度阈值: {score_threshold}")

    search_kwargs.update(kwargs)

    try:
        retriever = vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

        logger.info("检索器创建成功")
        return retriever

    except Exception as e:
        logger.error(f"创建检索器失败: {e}")
        raise

def create_retriever_tool(
    retriever: BaseRetriever,
    name: str = "knowledge_base",
    description: Optional[str] = None,
) -> any:
    """将检索器封装为 LangChain Tool

    将检索器转换为 LangChain Tool，使其可以被 Agent 或其他组件使用。

    Args:
        retriever (BaseRetriever): 检索器实例
        name (str): 工具名称，用于标识和调用该工具
            默认值: "knowledge_base"
        description (Optional[str]): 工具描述，帮助 Agent 理解何时以及如何使用该工具
            如果为 None 则使用默认描述
            默认值: None

    Returns:
        Tool: LangChain Tool 实例，可作为 Agent 的工具使用

    Raises:
        Exception: 创建工具失败时抛出异常

    Note:
        - 默认描述强调在需要准确信息来源时应该使用此工具
        - Tool 会自动将查询文本传递给检索器
        - 返回的文档内容会作为工具的输出

    Example:
        >>> retriever = create_retriever(vector_store)
        >>> tool = create_retriever_tool(
        >>>     retriever,
        >>>     name="tech_docs",
        >>>     description="搜索技术文档中的相关信息"
        >>> )
        >>> # 将工具添加到 Agent
        >>> agent = create_agent(tools=[tool])
    """
    if description is None:
        description = (
            f"搜索知识库 '{name}' 中的相关文档和信息。"
            f"当用户询问关于知识库中内容的问题时，必须使用此工具来获取准确信息。"
            f"输入应该是用户的查询或问题，工具将返回相关的文档片段。"
            f"重要：如果问题涉及特定文档、项目细节或需要准确的信息来源，请优先使用此工具。"
        )

    logger.info(f"创建检索器工具: {name}")
    logger.debug(f"描述: {description}")

    try:
        tool = lc_create_retriever_tool(
            retriever=retriever,
            name=name,
            description=description,
        )

        logger.info("检索器工具创建成功")
        return tool

    except Exception as e:
        logger.error(f"创建检索器工具失败: {e}")
        raise

def create_multi_retriever(
    retrievers: list[tuple[BaseRetriever, float]],
    **kwargs: object,
) -> BaseRetriever:
    """创建多检索器

    创建一个集成多个检索器的组合检索器，通过加权平均合并检索结果。

    Args:
        retrievers (list[tuple[BaseRetriever, float]]): 检索器及其权重的列表
            每个元素是一个元组：(检索器实例, 权重)
            权重用于控制每个检索器对最终结果的影响程度
        **kwargs: 传递给 EnsembleRetriever 的其他参数

    Returns:
        BaseRetriever: 组合检索器实例

    Raises:
        ImportError: 当 EnsembleRetriever 不可用时抛出异常
        Exception: 创建组合检索器失败时抛出异常

    Note:
        - 使用 EnsembleRetriever 实现多检索器组合
        - 每个检索器的权重会归一化，总和为 1.0
        - 权重越高的检索器对最终结果影响越大
        - 适用于需要结合多种检索策略的场景

    Example:
        >>> retriever1 = create_retriever(vs1, search_type="similarity")
        >>> retriever2 = create_retriever(vs2, search_type="mmr")
        >>> # 创建组合检索器，第一个权重为 0.7，第二个为 0.3
        >>> ensemble = create_multi_retriever([
        >>>     (retriever1, 0.7),
        >>>     (retriever2, 0.3)
        >>> ])
        >>> docs = ensemble.invoke("查询问题")
    """
    try:
        logger.info(f"创建组合检索器: {len(retrievers)} 个检索器")
        retriever_list = [r for r, _ in retrievers]
        weights = [w for _, w in retrievers]
        ensemble = EnsembleRetriever(
            retrievers=retriever_list,
            weights=weights,
            **kwargs,
        )
        logger.info("组合检索器创建成功")
        return ensemble

    except ImportError:
        logger.error("EnsembleRetriever 不可用")
        raise

    except Exception as e:
        logger.error(f"创建组合检索器失败: {e}")
        raise

def get_retriever_config(search_type: str = "similarity") -> dict:
    """获取推荐的检索器配置

    返回针对不同检索类型优化的推荐配置参数。

    Args:
        search_type (str): 检索类型，支持:
            - "similarity": 基本相似度检索
            - "mmr": 最大边际相关性检索
            - "threshold": 相似度阈值过滤
            默认值: "similarity"

    Returns:
        dict: 推荐的配置参数字典，包含:
            - search_type (str): 检索类型
            - k (int): 返回的文档数量
            - fetch_k (int): MMR 检索时获取的文档数量（仅 mmr）
            - score_threshold (float): 相似度阈值（仅 threshold）

    Note:
        - 如果传入未知的检索类型，会记录警告并返回 similarity 的配置
        - 这些配置是经过优化的推荐值，可以根据具体需求调整
        - 返回的配置中不包含 description 字段

    Example:
        >>> # 获取 MMR 检索的推荐配置
        >>> config = get_retriever_config("mmr")
        >>> retriever = create_retriever(vector_store, **config)
        >>>
        >>> # 获取阈值过滤的推荐配置
        >>> config = get_retriever_config("threshold")
        >>> retriever = create_retriever(vector_store, **config)
    """
    configs = {
        "similarity": {
            "search_type": "similarity",
            "k": 4,
            "description": "基本相似度检索，速度快",
        },
        "mmr": {
            "search_type": "mmr",
            "k": 4,
            "fetch_k": 20,
            "description": "最大边际相关性检索，结果更多样化",
        },
        "threshold": {
            "search_type": "similarity_score_threshold",
            "score_threshold": 0.7,
            "k": 10,
            "description": "相似度阈值过滤，只返回高质量结果",
        },
    }

    if search_type not in configs:
        logger.warning(f"未知的检索类型: {search_type}，使用默认配置")
        return configs["similarity"]

    config = configs[search_type].copy()
    logger.info(f"推荐的检索器配置 ({search_type}):")
    logger.info(f"{config.get('description', '')}")
    config.pop("description", None)
    return config