"""文本分块器模块

该模块提供了多种文本分块策略，用于将大文档切分为适合向量检索的小块。
支持多种分块算法和针对不同文档类型的优化配置。

主要功能:
    - get_text_splitter: 获取指定类型的文本分块器
    - split_documents: 对文档列表进行分块
    - split_text: 对纯文本进行分块
    - get_optimal_chunk_size: 根据文档类型获取推荐的分块参数
    - analyze_chunks: 分析分块结果的统计信息

支持的分割器类型:
    - recursive: 递归分割（推荐），使用多种分隔符智能分割
    - character: 按字符分割，使用单个分隔符
    - markdown: 专门针对 Markdown 格式优化
    - token: 按令牌（token）数量分割

Example:
    >>> from blues_aka.rag.splitters import split_documents, get_optimal_chunk_size
    >>> # 使用推荐的分块参数
    >>> chunk_size, overlap = get_optimal_chunk_size("code")
    >>> chunks = split_documents(documents, chunk_size=chunk_size, chunk_overlap=overlap)
    >>> print(f"生成了 {len(chunks)} 个文本块")
"""
import logging
from typing import Literal, List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter, MarkdownTextSplitter, \
    TokenTextSplitter

logger = logging.getLogger(__name__)

# 分割器类型字面量类型
SplitterType = Literal["recursive", "character", "markdown", "token"]


# ==================== 配置辅助函数 ====================

def _get_config():
    """延迟获取配置，避免循环导入

    Returns:
        配置对象实例
    """
    from blues_aka import ConfigFactory
    return ConfigFactory.get_config()


_config = None


def _get_default_chunk_size() -> int:
    """获取默认的分块大小

    Returns:
        int: 配置文件中的默认分块大小
    """
    global _config
    if _config is None:
        _config = _get_config()
    return _config.chunk_size


def _get_default_chunk_overlap() -> int:
    """获取默认的分块重叠

    Returns:
        int: 配置文件中的默认分块重叠大小
    """
    global _config
    if _config is None:
        _config = _get_config()
    return _config.chunk_overlap


# ==================== 主要功能函数 ====================

def get_text_splitter(
    splitter_type: SplitterType = "recursive",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    **kwargs,
):
    """获取文本分块器

    创建并返回一个指定类型的文本分块器实例。

    Args:
        splitter_type (SplitterType): 分割器类型，支持:
            - "recursive": 递归分割（推荐），智能使用多种分隔符
            - "character": 按字符分割，使用单个分隔符
            - "markdown": 专门针对 Markdown 格式优化
            - "token": 按令牌（token）数量分割
            默认值: "recursive"
        chunk_size (Optional[int]): 每个文本块的最大字符数
            如果为 None 则使用配置文件中的默认值
            默认值: None
        chunk_overlap (Optional[int]): 相邻文本块之间的重叠字符数
            如果为 None 则使用配置文件中的默认值
            默认值: None
        **kwargs: 传递给具体分割器类的其他参数

    Returns:
        文本分割器实例，具体类型取决于 splitter_type

    Raises:
        ValueError: 当传入不支持的分割器类型时抛出异常

    Note:
        - recursive: 最通用的选择，按优先级尝试 ["\n\n", "\n", " ", ""]
        - character: 简单但不够智能，使用 "\n\n" 作为分隔符
        - markdown: 保留 Markdown 结构，按标题、列表等分割
        - token: 基于 token 数量而非字符数，适合 LLM 处理

    Example:
        >>> # 创建递归分割器
        >>> splitter = get_text_splitter("recursive", chunk_size=1000, chunk_overlap=200)
        >>> chunks = splitter.split_text(long_text)
        >>>
        >>> # 创建 Markdown 分割器
        >>> splitter = get_text_splitter("markdown", chunk_size=800)
    """
    chunk_size = chunk_size or _get_default_chunk_size()
    chunk_overlap = chunk_overlap or _get_default_chunk_overlap()

    logger.debug(
        f"创建文本分块器: type={splitter_type}, "
        f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
    )

    if splitter_type == "recursive":
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            **kwargs,
        )

    elif splitter_type == "character":
        return CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n\n",
            length_function=len,
            is_separator_regex=False,
            **kwargs,
        )

    elif splitter_type == "markdown":
        return MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        )

    elif splitter_type == "token":
        return TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        )

    else:
        raise ValueError(
            f"不支持的分块器类型: {splitter_type}。"
            f"支持的类型: recursive, character, markdown, token"
        )

def split_documents(
    documents: List[Document],
    splitter_type: SplitterType = "recursive",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    **kwargs,
) -> List[Document]:
    """文本分块列表

    对文档列表进行分块处理，将长文档分割成适合向量检索的小块。

    Args:
        documents (List[Document]): 要分块的文档列表
        splitter_type (SplitterType): 分割器类型
            默认值: "recursive"
        chunk_size (Optional[int]): 每个文本块的最大字符数
            默认值: None (使用配置文件中的默认值)
        chunk_overlap (Optional[int]): 相邻文本块之间的重叠字符数
            默认值: None (使用配置文件中的默认值)
        **kwargs: 传递给分割器的其他参数

    Returns:
        List[Document]: 分块后的文档列表，包含原始文档的所有元数据

    Raises:
        Exception: 分块失败时抛出异常

    Note:
        - 如果文档列表为空，返回空列表并记录警告日志
        - 分块后的文档会保留原始文档的元数据
        - 会记录分块统计信息：总块数、平均块大小、总字符数

    Example:
        >>> from blues_aka.rag.loader import load_document
        >>> from blues_aka.rag.splitters import split_documents
        >>>
        >>> docs = load_document("large_document.pdf")
        >>> chunks = split_documents(
        >>>     docs,
        >>>     splitter_type="recursive",
        >>>     chunk_size=1000,
        >>>     chunk_overlap=200
        >>> )
        >>> print(f"将 {len(docs)} 个文档分割为 {len(chunks)} 个块")
    """
    if not documents:
        logger.warning("文档列表为空，无需分块")
        return []

    logger.info(f"开始分块: {len(documents)} 个文档")

    splitter = get_text_splitter(
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs,
    )

    try:
        chunks = splitter.split_documents(documents)
        logger.info(f"分块完成: {len(chunks)} 个文本块")

        total_chars = sum(len(chunk.page_content) for chunk in chunks)
        average_chars = total_chars / len(chunks) if chunks else 0

        logger.info(f"平均块大小: {average_chars:.0f} 字符")
        logger.info(f"总字符数: {total_chars}")

        return chunks

    except Exception as e:
        logger.error(f"分块失败: {e}")
        raise

def split_text(
    text: str,
    splitter_type: SplitterType = "recursive",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    metadata: Optional[dict] = None,
    **kwargs,
) -> List[Document]:
    """分块纯文本

    将纯文本字符串分割成多个文档块。

    Args:
        text (str): 要分块的纯文本内容
        splitter_type (SplitterType): 分割器类型
            默认值: "recursive"
        chunk_size (Optional[int]): 每个文本块的最大字符数
            默认值: None (使用配置文件中的默认值)
        chunk_overlap (Optional[int]): 相邻文本块之间的重叠字符数
            默认值: None (使用配置文件中的默认值)
        metadata (Optional[dict]): 要添加到每个文档块的元数据
            默认值: None
        **kwargs: 传递给分割器的其他参数

    Returns:
        List[Document]: 分块后的文档列表

    Raises:
        Exception: 分块失败时抛出异常

    Note:
        - 如果文本为空，返回空列表并记录警告日志
        - 如果提供了 metadata，它会被添加到所有文档块中
        - 返回的是 Document 对象列表，而非纯文本

    Example:
        >>> long_text = "这是一段很长的文本..." * 100
        >>> chunks = split_text(
        >>>     long_text,
        >>>     splitter_type="recursive",
        >>>     chunk_size=500,
        >>>     chunk_overlap=50,
        >>>     metadata={"source": "user_input"}
        >>> )
        >>> print(f"生成了 {len(chunks)} 个文本块")
    """
    if not text:
        logger.warning("文本为空，无需分块")
        return []

    logger.info(f"开始分块文本: {len(text)} 字符")

    splitter = get_text_splitter(
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs,
    )

    try:
        metadatas = [metadata] if metadata else None
        chunks = splitter.create_documents([text], metadatas=metadatas)
        logger.info(f"分块完成: {len(chunks)} 个文本块")
        return chunks

    except Exception as e:
        logger.error(f"分块失败: {e}")
        raise

def get_optimal_chunk_size(
    document_type: str = "general",
) -> tuple[int, int]:
    """根据文档类型获取推荐的分块参数

    返回针对不同文档类型优化的推荐分块大小和重叠参数。

    Args:
        document_type (str): 文档类型，支持:
            - "general": 通用文档
            - "code": 代码文件（需要更大的上下文）
            - "markdown": Markdown 文档（结构清晰）
            - "academic": 学术论文（需要保持上下文）
            - "chat": 对话记录（可以更小）
            默认值: "general"

    Returns:
        tuple[int, int]: (chunk_size, chunk_overlap) 元组
            - chunk_size: 推荐的分块大小
            - chunk_overlap: 推荐的重叠大小

    Note:
        - 如果传入未知的文档类型，会记录警告并返回通用文档的配置
        - 这些参数是基于经验优化的推荐值，可根据具体需求调整

    Example:
        >>> # 代码文档的推荐配置
        >>> chunk_size, overlap = get_optimal_chunk_size("code")
        >>> splitter = get_text_splitter(chunk_size=chunk_size, chunk_overlap=overlap)
        >>>
        >>> # 学术论文的推荐配置
        >>> chunk_size, overlap = get_optimal_chunk_size("academic")
        >>> chunks = split_documents(docs, chunk_size=chunk_size, chunk_overlap=overlap)
    """
    recommendations = {
        "general": (1000, 200),      # 通用文档
        "code": (1500, 300),          # 代码需要更大的上下文
        "markdown": (800, 150),       # Markdown 通常结构清晰
        "academic": (1200, 250),      # 学术论文需要保持上下文
        "chat": (500, 50),            # 对话记录可以更小
    }

    if document_type not in recommendations:
        logger.warning(f"未知的文档类型: {document_type}，使用默认参数")
        return recommendations["general"]

    chunk_size, overlap = recommendations[document_type]

    logger.info(
        f"推荐的分块参数 ({document_type}): "
        f"chunk_size={chunk_size}, overlap={overlap}"
    )

    return chunk_size, overlap

def analyze_chunks(chunks: List[Document]) -> dict:
    """分析分块结果的统计信息

    计算并返回文档块的统计信息，帮助评估分块效果。

    Args:
        chunks (List[Document]): 文档块列表

    Returns:
        dict: 统计信息字典，包含:
            - total_chunks (int): 总块数
            - total_chars (int): 总字符数
            - avg_chunk_size (float): 平均块大小（字符数）
            - min_chunk_size (int): 最小块大小（字符数）
            - max_chunk_size (int): 最大块大小（字符数）

    Note:
        - 如果文档块列表为空，所有统计值返回 0
        - 会自动记录统计信息到日志
        - avg_chunk_size 保留浮点数精度

    Example:
        >>> chunks = split_documents(documents)
        >>> stats = analyze_chunks(chunks)
        >>> print(f"总共 {stats['total_chunks']} 个块")
        >>> print(f"平均大小: {stats['avg_chunk_size']:.0f} 字符")
        >>> print(f"大小范围: {stats['min_chunk_size']} - {stats['max_chunk_size']}")
    """
    if not chunks:
        return {
            "total_chunks": 0,
            "total_chars": 0,
            "avg_chunk_size": 0,
            "min_chunk_size": 0,
            "max_chunk_size": 0,
        }

    chunk_sizes = [len(chunk.page_content) for chunk in chunks]
    total_chars = sum(chunk_sizes)

    stats = {
        "total_chunks": len(chunks),
        "total_chars": total_chars,
        "avg_chunk_size": total_chars / len(chunks),
        "min_chunk_size": min(chunk_sizes),
        "max_chunk_size": max(chunk_sizes),
    }

    logger.info("分块统计:")
    logger.info(f"总块数: {stats['total_chunks']}")
    logger.info(f"总字符数: {stats['total_chars']}")
    logger.info(f"平均大小: {stats['avg_chunk_size']:.0f} 字符")
    logger.info(f"最小块: {stats['min_chunk_size']} 字符")
    logger.info(f"最大块: {stats['max_chunk_size']} 字符")

    return stats
