import logging
from typing import Dict

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

