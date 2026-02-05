"""向量索引管理模块

该模块提供了 IndexManager 类，用于管理向量存储索引的创建、加载、更新和删除操作。
支持索引元数据管理，并提供索引查询功能。

主要功能:
    - 创建新的向量索引
    - 加载已存在的索引
    - 向索引添加新文档
    - 删除索引
    - 列出所有索引
    - 获取索引详细信息

Example:
    >>> from blues_aka.rag.index_manager import IndexManager
    >>> from blues_aka.rag.embeddings import get_embeddings
    >>>
    >>> manager = IndexManager()
    >>> embeddings = get_embeddings()
    >>> # 创建索引
    >>> manager.create_index("my_index", documents, embeddings, description="我的索引")
    >>> # 加载索引
    >>> vector_store = manager.load_index("my_index", embeddings)
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from blues_aka.rag.vector_stores import create_vector_store, save_vector_store, delete_vector_store, load_vector_store, \
    add_documents_to_vector_store

logger = logging.getLogger(__name__)


class IndexManager:
    """向量索引管理器

    该类用于管理向量存储索引的完整生命周期，包括创建、加载、更新、删除等操作。
    每个索引都包含元数据信息，如创建时间、文档数量、描述等。

    Attributes:
        base_path (Path): 索引存储的基础路径

    Example:
        >>> manager = IndexManager(base_path="./indexes")
        >>> # 创建索引
        >>> manager.create_index("docs", documents, embeddings)
        >>> # 列出所有索引
        >>> indexes = manager.list_indexes()
        >>> # 加载索引
        >>> vector_store = manager.load_index("docs", embeddings)
    """

    def __init__(self, base_path: Optional[str] = None):
        """初始化索引管理器

        Args:
            base_path (Optional[str]): 索引存储的基础路径。
                如果为 None，则从配置文件中读取默认路径。
                默认值: None

        Note:
            - 如果基础路径不存在，会自动创建
            - 初始化成功后会记录日志
        """
        from blues_aka import ConfigFactory
        _config = ConfigFactory.get_config()

        self.base_path = Path(base_path or _config.vector_store_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"索引管理器初始化: {self.base_path}")

    def _get_index_path(self, name: str) -> Path:
        """获取索引的完整路径

        Args:
            name (str): 索引名称

        Returns:
            Path: 索引的完整文件系统路径
        """
        return self.base_path / name

    def _get_metadata_path(self, name: str) -> Path:
        """获取索引元数据文件路径

        Args:
            name (str): 索引名称

        Returns:
            Path: 元数据文件的完整路径 (metadata.json)
        """
        return self._get_index_path(name) / "metadata.json"

    def _save_metadata(
            self,
            name: str,
            metadata: Dict[str, Any],
    ) -> None:
        """保存索引元数据

        将索引的元数据信息保存到 JSON 文件中。

        Args:
            name (str): 索引名称
            metadata (Dict[str, Any]): 要保存的元数据字典

        Note:
            - 如果父目录不存在，会自动创建
            - 文件以 UTF-8 编码保存，格式化缩进为 2
        """
        metadata_path = self._get_metadata_path(name)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.debug(f"保存元数据: {metadata_path}")

    def _load_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """加载索引元数据

        从 JSON 文件中读取索引的元数据信息。

        Args:
            name (str): 索引名称

        Returns:
            Optional[Dict[str, Any]]: 元数据字典，如果文件不存在或加载失败则返回 None

        Note:
            - 如果元数据文件不存在，返回 None
            - 如果加载失败，记录错误日志并返回 None
        """
        metadata_path = self._get_metadata_path(name)

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            return metadata

        except Exception as e:
            logger.error(f"加载元数据失败: {e}")
            return None

    def create_index(
        self,
        name: str,
        documents: List[Document],
        embeddings: Embeddings,
        description: str = "",
        store_type: Optional[str] = None,
        overwrite: bool = False,
        **kwargs,
    ) -> VectorStore:
        """创建新索引

        使用给定的文档和嵌入模型创建一个新的向量索引。

        Args:
            name (str): 索引名称，用于标识和后续访问索引
            documents (List[Document]): 要添加到索引中的文档列表
            embeddings (Embeddings): 用于生成向量的嵌入模型
            description (str): 索引的描述信息
                默认值: ""
            store_type (Optional[str]): 向量存储类型，如果为 None 则使用配置文件中的默认值
                默认值: None
            overwrite (bool): 如果索引已存在，是否覆盖
                默认值: False
            **kwargs: 传递给向量存储的其他参数

        Returns:
            VectorStore: 创建的向量存储实例

        Raises:
            ValueError: 当索引已存在且 overwrite=False 时抛出异常
            Exception: 创建索引失败时抛出异常，并清理已创建的文件

        Note:
            - 创建的索引会自动保存到磁盘
            - 元数据包含创建时间、更新时间、文档数量等信息
            - 如果创建失败，会自动清理已创建的文件
        """
        from blues_aka import ConfigFactory
        _config = ConfigFactory.get_config()

        index_path = self._get_index_path(name)

        if index_path.exists() and not overwrite:
            raise ValueError(
                f"索引已存在: {name}。使用 overwrite=True 来覆盖。"
            )

        logger.info(f"创建索引: {name}")
        logger.info(f"文档数量: {len(documents)}")
        logger.info(f"描述: {description}")

        try:
            vector_store = create_vector_store(
                documents=documents,
                embeddings=embeddings,
                store_type=store_type,
                **kwargs,
            )
            save_vector_store(vector_store, str(index_path), embeddings)
            metadata = {
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "num_documents": len(documents),
                "store_type": store_type or _config.vector_store_type,
                "embedding_model": _config.embedding_model,
            }
            self._save_metadata(name, metadata)
            logger.info(f"索引创建成功: {name}")
            return vector_store

        except Exception as e:
            logger.error(f"创建索引失败: {e}")

            if index_path.exists():
                delete_vector_store(str(index_path))

            raise

    def load_index(
        self,
        name: str,
        embeddings: Embeddings,
        **kwargs,
    ) -> VectorStore:
        """加载索引

        从磁盘加载已存在的向量索引。

        Args:
            name (str): 要加载的索引名称
            embeddings (Embeddings): 用于生成向量的嵌入模型
            **kwargs: 传递给向量存储加载函数的其他参数

        Returns:
            VectorStore: 加载的向量存储实例

        Raises:
            FileNotFoundError: 当索引不存在时抛出异常
            Exception: 加载索引失败时抛出异常

        Note:
            - 加载成功后会记录索引的元数据信息（如果有）
            - 元数据包括描述和文档数量
        """
        index_path = self._get_index_path(name)

        if not index_path.exists():
            raise FileNotFoundError(f"索引不存在: {name}")

        logger.info(f"加载索引: {name}")

        try:
            metadata = self._load_metadata(name)

            if metadata:
                logger.info(f"描述: {metadata.get('description', 'N/A')}")
                logger.info(f"文档数: {metadata.get('num_documents', 'N/A')}")

            vector_store = load_vector_store(
                load_path=str(index_path),
                embeddings=embeddings,
                **kwargs,
            )
            logger.info(f"索引加载成功: {name}")
            return vector_store

        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            raise

    def update_index(
        self,
        name: str,
        documents: List[Document],
        embeddings: Embeddings,
        **kwargs,
    ) -> VectorStore:
        """更新索引（添加新文档）

        向已存在的索引中添加新文档，并保存更新后的索引。

        Args:
            name (str): 要更新的索引名称
            documents (List[Document]): 要添加的新文档列表
            embeddings (Embeddings): 用于生成向量的嵌入模型
            **kwargs: 传递给向量存储加载函数的其他参数

        Returns:
            VectorStore: 更新后的向量存储实例

        Raises:
            Exception: 更新索引失败时抛出异常

        Note:
            - 会自动更新索引的元数据（更新时间和文档数量）
            - 更新后的索引会自动保存到磁盘
        """
        logger.info(f"更新索引: {name}")
        logger.info(f"新增文档: {len(documents)}")

        try:
            vector_store = self.load_index(name, embeddings, **kwargs)
            add_documents_to_vector_store(vector_store, documents)
            index_path = self._get_index_path(name)
            save_vector_store(vector_store, str(index_path), embeddings)
            metadata = self._load_metadata(name) or {}
            metadata["updated_at"] = datetime.now().isoformat()
            metadata["num_documents"] = metadata.get("num_documents", 0) + len(documents)
            self._save_metadata(name, metadata)
            logger.info(f"索引更新成功: {name}")
            return vector_store

        except Exception as e:
            logger.error(f"更新索引失败: {e}")
            raise

    def delete_index(self, name: str) -> None:
        """删除索引

        从磁盘删除指定的向量索引及其所有相关文件。

        Args:
            name (str): 要删除的索引名称

        Raises:
            Exception: 删除索引失败时抛出异常

        Note:
            - 如果索引不存在，会记录警告日志并直接返回
            - 此操作不可逆，请谨慎使用
        """
        index_path = self._get_index_path(name)

        if not index_path.exists():
            logger.warning(f"索引不存在: {name}")
            return

        logger.info(f"删除索引: {name}")

        try:
            delete_vector_store(str(index_path))
            logger.info(f"索引删除成功: {name}")

        except Exception as e:
            logger.error(f"删除索引失败: {e}")
            raise

    def list_indexes(self) -> List[Dict[str, Any]]:
        """列出所有索引

        获取基础路径下所有索引的元数据信息列表。

        Returns:
            List[Dict[str, Any]]: 索引元数据列表，每个元素包含:
                - name (str): 索引名称
                - description (str): 索引描述
                - created_at (str): 创建时间
                - updated_at (str): 更新时间
                - num_documents (int): 文档数量

        Note:
            - 如果索引没有元数据文件，会使用默认值填充
            - 如果基础路径不存在，返回空列表
        """
        logger.info("列出所有索引")
        indexes = []

        if not self.base_path.exists():
            return indexes

        for index_path in self.base_path.iterdir():
            if not index_path.is_dir():
                continue

            name = index_path.name
            metadata = self._load_metadata(name) or {}

            if metadata:
                indexes.append(metadata)

            else:
                indexes.append({
                    "name": name,
                    "description": "N/A",
                    "created_at": "N/A",
                    "updated_at": "N/A",
                    "num_documents": "N/A",
                })

        logger.info(f"找到 {len(indexes)} 个索引")
        return indexes

    def get_index_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取索引详细信息

        获取指定索引的详细元数据信息，包括路径和大小。

        Args:
            name (str): 索引名称

        Returns:
            Optional[Dict[str, Any]]: 索引详细信息字典，包含:
                - name (str): 索引名称
                - description (str): 索引描述
                - created_at (str): 创建时间
                - updated_at (str): 更新时间
                - num_documents (int): 文档数量
                - path (str): 索引路径
                - size (int): 索引总大小（字节）
                - size_mb (float): 索引大小（MB）

            如果索引不存在，返回 None

        Note:
            - 如果索引没有元数据，只包含基本信息
            - 如果计算索引大小失败，会记录警告日志
        """
        index_path = self._get_index_path(name)

        if not index_path.exists():
            logger.warning(f"索引不存在: {name}")
            return None

        metadata = self._load_metadata(name) or {}

        if not metadata:
            metadata = {
                "name": name,
                "description": "N/A",
            }

        metadata["path"] = str(index_path)

        try:
            totle_size = sum(
                f.stat().st_size
                for f in index_path.rglob("*")
                if f.is_file()
            )
            metadata["size"] = totle_size
            metadata["size_mb"] = totle_size / 1024 / 1024

        except Exception as e:
            logger.warning(f"计算索引大小失败: {e}")

        return metadata

    def index_exists(self, name: str) -> bool:
        """检查索引是否存在

        检查指定名称的索引是否存在于基础路径中。

        Args:
            name (str): 索引名称

        Returns:
            bool: 如果索引存在返回 True，否则返回 False

        Example:
            >>> if manager.index_exists("my_index"):
            >>>     vector_store = manager.load_index("my_index", embeddings)
        """
        return self._get_index_path(name).exists()