import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, UnstructuredHTMLLoader, JSONLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# 支持的文件扩展名映射
SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".txt": "text",
    ".md": "markdown",
    ".mdx": "markdown",
    ".html": "html",
    ".htm": "html",
    ".json": "json",
}

def get_supported_extensions() -> Dict[str, str]:
    """获取支持的文件格式"""
    return SUPPORTED_EXTENSIONS.copy()

def get_loader_for_file(file_path: str) -> Optional[Any]:
    """根据文件类型获取合适的文档加载器"""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        logger.error(f"Unsupported file extension: {file_path}")
        return None

    file_type = SUPPORTED_EXTENSIONS[extension]

    try:
        if file_type == "pdf":
            return PyPDFLoader(str(file_path))
        elif file_type == "txt":
            return TextLoader(str(file_path), encoding="utf-8")
        elif file_type == "md":
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
    """加载单个文档"""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"不是文件: {file_path}")

    loader = get_loader_for_file(file_path)

    if loader is None:
        extension = file_path.suffix.lower()
        supported = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise ValueError(
            f"不支持的文件类型: {extension}。"
            f"支持的类型: {supported}"
        )

    try:
        documents = loader.load()
        if add_metadata:
            for doc in documents:
                if doc.metadata is None:
                    doc.metadata = {}
                doc.metadata.update({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "file_type": SUPPORTED_EXTENSIONS[file_path.suffix.lower()],
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
    """批量加载目录中的文档"""
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
    """从文件路径列表加载文档"""
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