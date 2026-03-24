"""文档加载器模块

该模块提供了多种文件格式的文档加载功能，支持 PDF、文本、Markdown、HTML 和 JSON 格式。
可以加载单个文件或批量加载目录中的多个文件。

主要功能:
    - get_supported_extensions: 获取支持的文件格式列表
    - get_loader_for_file: 根据文件类型获取相应的加载器
    - load_document: 加载单个文档
    - load_directory: 批量加载目录中的文档
    - load_documents_from_paths: 从文件路径列表加载文档

支持的文件格式:
    - PDF (.pdf): 使用 PyPDFLoader
    - 文本 (.txt): 使用 TextLoader
    - Markdown (.md, .mdx): 使用 UnstructuredMarkdownLoader
    - HTML (.html, .htm): 使用 UnstructuredHTMLLoader
    - JSON (.json): 使用 JSONLoader

Example:
    >>> from blues_aka.rag.loader import load_document, load_directory
    >>> # 加载单个文件
    >>> docs = load_document("document.pdf")
    >>> # 加载整个目录
    >>> docs = load_directory("./documents", recursive=True)
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, UnstructuredHTMLLoader, JSONLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# 支持的文件扩展名映射
SUPPORTED_EXTENSIONS: Dict[str, str] = {
    ".pdf": "pdf",
    ".txt": "text",
    ".md": "markdown",
    ".mdx": "markdown",
    ".html": "html",
    ".htm": "html",
    ".json": "json",
}


def get_supported_extensions() -> Dict[str, str]:
    """获取支持的文件格式

    返回支持的文件扩展名及其对应的文件类型映射。

    Returns:
        Dict[str, str]: 文件扩展名到文件类型的映射字典。
            键为文件扩展名（如 ".pdf"），值为文件类型（如 "pdf"）

    Example:
        >>> extensions = get_supported_extensions()
        >>> print(extensions)  # {'.pdf': 'pdf', '.txt': 'text', ...}
    """
    return SUPPORTED_EXTENSIONS.copy()


def get_loader_for_file(file_path: str) -> Optional[Any]:
    """根据文件类型获取合适的文档加载器

    根据文件扩展名自动选择并创建相应的文档加载器实例。

    Args:
        file_path (str): 文件路径

    Returns:
        Optional[Any]: 对应的文档加载器实例，如果文件类型不支持则返回 None

    Note:
        - PDF: PyPDFLoader
        - TXT: TextLoader (UTF-8 编码)
        - Markdown: UnstructuredMarkdownLoader
        - HTML: UnstructuredHTMLLoader
        - JSON: JSONLoader (使用 jq_schema=".")

    Example:
        >>> loader = get_loader_for_file("document.pdf")
        >>> if loader:
        >>>     docs = loader.load()
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower().strip()  # 清理扩展名：去除尾部空格

    if extension not in SUPPORTED_EXTENSIONS:
        logger.error(f"Unsupported file extension: {file_path}, extension: '{extension}'")
        logger.error(f"Supported extensions: {list(SUPPORTED_EXTENSIONS.keys())}")
        return None

    file_type = SUPPORTED_EXTENSIONS[extension]

    try:
        if file_type == "pdf":
            return PyPDFLoader(str(file_path))
        elif file_type == "text":
            return TextLoader(str(file_path), encoding="utf-8")
        elif file_type == "markdown":
            return UnstructuredMarkdownLoader(str(file_path))
        elif file_type == "html":
            return UnstructuredHTMLLoader(str(file_path))
        elif file_type == "json":
            return JSONLoader(
                str(file_path),
                jq_schema=".",
                text_content=False,
            )
        else:
            logger.warning(f"未实现的文件类型处理: {file_type}")
            return None

    except Exception as e:
        logger.error(f"创建加载器失败: {file_path}, 错误: {e}")
        return None

def load_document(
    file_path: str,
    add_metadata: bool = True,
) -> List[Document]:
    """加载单个文档

    从指定路径加载文档，并可选地添加元数据信息。

    Args:
        file_path (str): 文件路径
        add_metadata (bool): 是否自动添加元数据（包括源文件路径、文件名、文件类型）
            默认值: True

    Returns:
        List[Document]: 加载的文档列表，一个文件可能被分割成多个文档块

    Raises:
        FileNotFoundError: 当文件不存在时抛出异常
        ValueError: 当路径不是文件或文件类型不支持时抛出异常
        Exception: 加载文档失败时抛出异常

    Note:
        - 添加的元数据包括:
            - source: 文件完整路径
            - filename: 文件名
            - file_type: 文件类型
        - 不同文件类型可能产生不同数量的文档块

    Example:
        >>> docs = load_document("report.pdf")
        >>> print(f"加载了 {len(docs)} 个文档块")
        >>> print(docs[0].metadata)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"不是文件: {file_path}")

    loader = get_loader_for_file(file_path)

    if loader is None:
        extension = file_path.suffix.lower().strip()  # 清理扩展名
        supported = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise ValueError(
            f"不支持的文件类型: {extension}。"
            f"支持的类型: {supported}"
        )

    try:
        documents = loader.load()
        if add_metadata:
            # 清理扩展名用于元数据
            clean_extension = file_path.suffix.lower().strip()
            for doc in documents:
                if doc.metadata is None:
                    doc.metadata = {}
                doc.metadata.update({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "file_type": SUPPORTED_EXTENSIONS[clean_extension],
                })

        logger.info(f"成功加载 {len(documents)} 个文档块")
        return documents

    except Exception as e:
        logger.error(f"加载文档失败: {file_path}, 错误: {e}")
        raise

def load_directory(
    directory_path: str,
    glob_pattern: str = "**/*",
    exclude_patterns: Optional[List[str]] = None,
    recursive: bool = True,
    show_progress: bool = True,
    max_files: Optional[int] = None,
) -> List[Document]:
    """批量加载目录中的文档

    从指定目录递归或非递归地加载所有支持的文件。

    Args:
        directory_path (str): 目录路径
        glob_pattern (str): 文件匹配模式，用于筛选文件
            默认值: "**/*"
        exclude_patterns (Optional[List[str]]): 要排除的文件模式列表，支持通配符
            默认值: None
        recursive (bool): 是否递归加载子目录中的文件
            默认值: True
        show_progress (bool): 是否显示加载进度信息
            默认值: True
        max_files (Optional[int]): 最大加载文件数量，超过限制时只加载前 N 个文件
            默认值: None

    Returns:
        List[Document]: 所有文件加载的文档列表

    Raises:
        FileNotFoundError: 当目录不存在时抛出异常
        ValueError: 当路径不是目录时抛出异常

    Note:
        - 自动跳过不支持的文件类型
        - 单个文件加载失败不会中断整个批量加载过程
        - 加载完成后会记录成功和失败的文件数量

    Example:
        >>> # 递归加载整个目录
        >>> docs = load_directory("./documents", recursive=True)
        >>> # 加载并排除某些文件
        >>> docs = load_directory(
        >>>     "./documents",
        >>>     exclude_patterns=["*.tmp", "*.bak"],
        >>>     max_files=100
        >>> )
    """
    directory_path = Path(directory_path)

    if not directory_path.exists():
        raise FileNotFoundError(f"目录不存在: {directory_path}")

    if not directory_path.is_dir():
        raise ValueError(f"不是目录: {directory_path}")

    logger.info(f"开始加载目录: {directory_path}")
    logger.info(f"匹配模式: {glob_pattern}")
    if exclude_patterns:
        logger.info(f"排除模式: {exclude_patterns}")

    all_files = []
    for ext in SUPPORTED_EXTENSIONS.keys():
        pattern = f"**/*{ext}*" if recursive else f"*{ext}"
        files = list(directory_path.glob(pattern))
        all_files.extend(files)

    if exclude_patterns:
        filtered_files = []
        for file in all_files:
            should_exclude = False
            for pattern in exclude_patterns:
                if file.match(pattern):
                    should_exclude = True
                    break
            if not should_exclude:
                filtered_files.append(file)
        all_files = filtered_files

    if max_files is not None and len(all_files) > max_files:
        logger.warning(f"文件数量 ({len(all_files)}) 超过限制 ({max_files})，只加载前 {max_files} 个")
        all_files = all_files[:max_files]

    all_documents = []
    success_count = 0
    error_count = 0

    for i, file in enumerate(all_files, 1):
        try:
            if show_progress:
                logger.info(f"[{i}/{len(all_files)}] 加载: {file.name}")

            documents = load_document(str(file), add_metadata=True)
            all_documents.extend(documents)
            success_count += 1

        except Exception as e:
            logger.error(f"加载失败: {file.name}, 错误: {e}")
            error_count += 1
            continue

    logger.info(f"目录加载完成:")
    logger.info(f"成功: {success_count} 个文件")
    logger.info(f"失败: {error_count} 个文件")
    logger.info(f"总计: {len(all_documents)} 个文档块")

    return all_documents

def load_documents_from_paths(
    file_paths: List[str],
    show_progress: bool = True,
) -> List[Document]:
    """从文件路径列表加载文档

    批量加载多个指定路径的文档文件。

    Args:
        file_paths (List[str]): 文件路径列表
        show_progress (bool): 是否显示加载进度信息
            默认值: True

    Returns:
        List[Document]: 所有文件加载的文档列表

    Note:
        - 单个文件加载失败不会中断整个批量加载过程
        - 加载完成后会记录成功和失败的文件数量
        - 自动为每个文档添加元数据信息

    Example:
        >>> files = ["doc1.pdf", "doc2.txt", "doc3.md"]
        >>> docs = load_documents_from_paths(files)
        >>> print(f"总共加载了 {len(docs)} 个文档块")
    """
    logger.info(f"开始加载 {len(file_paths)} 个文件")

    all_documents = []
    success_count = 0
    error_count = 0

    for i, file_path in enumerate(file_paths, 1):
        try:
            if show_progress:
                logger.info(f"[{i}/{len(file_paths)}] 加载: {Path(file_path).name}")

            documents = load_document(file_path, add_metadata=True)
            all_documents.extend(documents)
            success_count += 1

        except Exception as e:
            logger.error(f"加载失败: {file_path}, 错误: {e}")
            error_count += 1
            continue

    logger.info(f"批量加载完成:")
    logger.info(f"成功: {success_count} 个文件")
    logger.info(f"失败: {error_count} 个文件")
    logger.info(f"总计: {len(all_documents)} 个文档块")

    return all_documents