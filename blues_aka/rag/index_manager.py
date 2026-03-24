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

            # 记录版本变更
            self._record_version(
                name=name,
                change_type="created",
                num_documents=len(documents),
                description=f"创建索引，共 {len(documents)} 个文档"
            )

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
            new_doc_count = metadata.get("num_documents", 0) + len(documents)
            metadata["updated_at"] = datetime.now().isoformat()
            metadata["num_documents"] = new_doc_count
            self._save_metadata(name, metadata)

            # 记录版本变更
            self._record_version(
                name=name,
                change_type="updated",
                num_documents=new_doc_count,
                description=f"添加 {len(documents)} 个文档"
            )

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

    # ==================== 版本管理功能 ====================

    def _generate_version(self) -> str:
        """生成版本号

        基于当前时间生成版本号，格式: v1.0.0-YYYYMMDDHHMMSS

        Returns:
            str: 版本号字符串
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d%H%M%S")
        return f"v1.0.0-{date_str}"

    def get_index_versions(self, name: str) -> List[Dict[str, Any]]:
        """获取索引的所有版本历史

        Args:
            name (str): 索引名称

        Returns:
            List[Dict[str, Any]]: 版本历史列表，每个版本包含:
                - version (str): 版本号
                - timestamp (str): 更新时间
                - num_documents (int): 文档数量
                - change_type (str): 变更类型 (created/updated)

        Note:
            - 从 history.json 文件读取版本历史
            - 如果文件不存在，返回空列表
        """
        history_path = self._get_index_path(name) / "history.json"

        if not history_path.exists():
            return []

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            return history.get("versions", [])

        except Exception as e:
            logger.error(f"读取版本历史失败: {e}")
            return []

    def _record_version(
        self,
        name: str,
        change_type: str,
        num_documents: int,
        description: str = ""
    ) -> None:
        """记录版本变更

        Args:
            name (str): 索引名称
            change_type (str): 变更类型 (created/updated/rebuilt)
            num_documents (int): 当前文档数量
            description (str): 变更描述
        """
        history_path = self._get_index_path(name) / "history.json"

        try:
            # 加载现有历史
            if history_path.exists():
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            else:
                history = {"versions": []}

            # 添加新版本
            version_entry = {
                "version": self._generate_version(),
                "timestamp": datetime.now().isoformat(),
                "change_type": change_type,
                "num_documents": num_documents,
                "description": description,
            }

            history["versions"].append(version_entry)

            # 限制历史记录数量（保留最近50条）
            if len(history["versions"]) > 50:
                history["versions"] = history["versions"][-50:]

            # 保存历史
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

            logger.debug(f"记录版本变更: {name} - {version_entry['version']}")

        except Exception as e:
            logger.error(f"记录版本变更失败: {e}")

    # ==================== 增量更新功能 ====================

    def update_index_incremental(
        self,
        name: str,
        embeddings: Embeddings,
        add_documents: Optional[List[Document]] = None,
        delete_document_ids: Optional[List[str]] = None,
        **kwargs,
    ) -> VectorStore:
        """增量更新索引

        支持添加和删除文档，无需重建整个索引。

        Args:
            name (str): 要更新的索引名称
            embeddings (Embeddings): 用于生成向量的嵌入模型
            add_documents (Optional[List[Document]]): 要添加的新文档列表
                默认值: None
            delete_document_ids (Optional[List[str]]): 要删除的文档ID列表
                默认值: None
            **kwargs: 传递给向量存储的其他参数

        Returns:
            VectorStore: 更新后的向量存储实例

        Raises:
            FileNotFoundError: 当索引不存在时抛出异常
            Exception: 更新索引失败时抛出异常

        Note:
            - 至少需要提供 add_documents 或 delete_document_ids 之一
            - 会自动记录版本变更
            - 更新操作会先添加后删除，确保原子性
        """
        if not add_documents and not delete_document_ids:
            raise ValueError("至少需要提供 add_documents 或 delete_document_ids")

        logger.info(f"增量更新索引: {name}")

        try:
            vector_store = self.load_index(name, embeddings, **kwargs)
            metadata = self._load_metadata(name) or {}
            current_doc_count = metadata.get("num_documents", 0)
            changes = []

            # 添加新文档
            if add_documents:
                logger.info(f"添加 {len(add_documents)} 个新文档")
                add_documents_to_vector_store(vector_store, add_documents)
                changes.append(f"添加 {len(add_documents)} 个文档")

            # 删除文档（如果向量存储支持）
            if delete_document_ids:
                logger.info(f"删除 {len(delete_document_ids)} 个文档")
                try:
                    # 尝试使用 delete 方法
                    if hasattr(vector_store, "delete"):
                        vector_store.delete(delete_document_ids)
                        changes.append(f"删除 {len(delete_document_ids)} 个文档")
                    else:
                        logger.warning("当前向量存储类型不支持删除操作")

                except Exception as e:
                    logger.error(f"删除文档失败: {e}")

            # 保存更新后的索引
            index_path = self._get_index_path(name)
            save_vector_store(vector_store, str(index_path), embeddings)

            # 更新元数据
            new_doc_count = current_doc_count + (len(add_documents) if add_documents else 0)
            metadata["updated_at"] = datetime.now().isoformat()
            metadata["num_documents"] = new_doc_count
            self._save_metadata(name, metadata)

            # 记录版本变更
            self._record_version(
                name=name,
                change_type="updated",
                num_documents=new_doc_count,
                description="; ".join(changes)
            )

            logger.info(f"索引增量更新成功: {name}")
            return vector_store

        except FileNotFoundError:
            logger.error(f"索引不存在: {name}")
            raise
        except Exception as e:
            logger.error(f"增量更新索引失败: {e}")
            raise

    def rebuild_index(
        self,
        name: str,
        documents: List[Document],
        embeddings: Embeddings,
        description: str = "",
        store_type: Optional[str] = None,
        **kwargs,
    ) -> VectorStore:
        """重建索引

        完全重建索引，替换所有现有内容。

        Args:
            name (str): 要重建的索引名称
            documents (List[Document]): 新的文档列表
            embeddings (Embeddings): 用于生成向量的嵌入模型
            description (str): 索引的描述信息
            store_type (Optional[str]): 向量存储类型
            **kwargs: 传递给向量存储的其他参数

        Returns:
            VectorStore: 重建后的向量存储实例

        Note:
            - 会备份当前索引到 {name}_backup
            - 重建失败会自动恢复备份
            - 会记录版本变更
        """
        logger.info(f"重建索引: {name}")

        # 备份现有索引
        backup_path = None
        if self.index_exists(name):
            backup_path = self._get_index_path(f"{name}_backup")
            index_path = self._get_index_path(name)

            try:
                import shutil
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(index_path, backup_path)
                logger.info(f"备份现有索引到: {backup_path}")

            except Exception as e:
                logger.warning(f"备份索引失败: {e}")

        try:
            # 使用 create_index 的逻辑，但标记为重建
            from blues_aka import ConfigFactory
            _config = ConfigFactory.get_config()

            index_path = self._get_index_path(name)

            vector_store = create_vector_store(
                documents=documents,
                embeddings=embeddings,
                store_type=store_type,
                **kwargs,
            )
            save_vector_store(vector_store, str(index_path), embeddings)

            # 获取旧描述或使用新描述
            old_metadata = self._load_metadata(name) or {}
            final_description = description or old_metadata.get("description", "")

            metadata = {
                "name": name,
                "description": final_description,
                "created_at": old_metadata.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "num_documents": len(documents),
                "store_type": store_type or _config.vector_store_type,
                "embedding_model": _config.embedding_model,
            }
            self._save_metadata(name, metadata)

            # 记录版本变更
            self._record_version(
                name=name,
                change_type="rebuilt",
                num_documents=len(documents),
                description=f"重建索引，共 {len(documents)} 个文档"
            )

            logger.info(f"索引重建成功: {name}")

            # 删除备份
            if backup_path and backup_path.exists():
                import shutil
                shutil.rmtree(backup_path)
                logger.info("已删除备份")

            return vector_store

        except Exception as e:
            logger.error(f"重建索引失败: {e}")

            # 恢复备份
            if backup_path and backup_path.exists():
                try:
                    import shutil
                    index_path = self._get_index_path(name)
                    if index_path.exists():
                        shutil.rmtree(index_path)
                    shutil.copytree(backup_path, index_path)
                    logger.info("已从备份恢复")

                except Exception as restore_error:
                    logger.error(f"恢复备份失败: {restore_error}")

            raise

    # ==================== 健康检查功能 ====================

    def check_index_health(self, name: str, embeddings: Optional[Embeddings] = None) -> Dict[str, Any]:
        """检查索引健康状态

        检测索引是否存在问题，如空索引、损坏、过时等。

        Args:
            name (str): 要检查的索引名称
            embeddings (Optional[Embeddings]): 嵌入模型，如果提供则进行深度检查
                默认值: None

        Returns:
            Dict[str, Any]: 健康检查报告，包含:
                - healthy (bool): 总体健康状态
                - issues (List[str]): 发现的问题列表
                - warnings (List[str]): 警告信息列表
                - info (Dict[str, Any]): 索引基本信息
                - recommendations (List[str]): 修复建议

        Example:
            >>> health = manager.check_index_health("my_index")
            >>> if not health["healthy"]:
            >>>     print("问题:", health["issues"])
            >>>     print("建议:", health["recommendations"])
        """
        health_report = {
            "healthy": True,
            "issues": [],
            "warnings": [],
            "info": {},
            "recommendations": [],
        }

        try:
            # 基本检查
            index_path = self._get_index_path(name)

            if not index_path.exists():
                health_report["healthy"] = False
                health_report["issues"].append("索引不存在")
                health_report["recommendations"].append("使用 create_index 创建索引")
                return health_report

            # 加载元数据
            metadata = self._load_metadata(name)
            if not metadata:
                health_report["warnings"].append("缺少元数据文件")
                health_report["recommendations"].append("考虑重建索引以恢复元数据")
            else:
                health_report["info"] = metadata

                # 检查文档数量
                num_docs = metadata.get("num_documents", 0)
                if num_docs == 0:
                    health_report["healthy"] = False
                    health_report["issues"].append("索引为空（没有文档）")
                    health_report["recommendations"].append("使用 update_index 添加文档")

                # 检查更新时间
                updated_at = metadata.get("updated_at", "")
                if updated_at:
                    try:
                        update_date = datetime.fromisoformat(updated_at)
                        days_old = (datetime.now() - update_date).days
                        health_report["info"]["days_since_update"] = days_old

                        if days_old > 30:
                            health_report["warnings"].append(
                                f"索引已 {days_old} 天未更新"
                            )
                            health_report["recommendations"].append("考虑更新索引内容")

                    except ValueError:
                        health_report["warnings"].append("无法解析更新时间")

            # 深度检查（如果提供了 embeddings）
            if embeddings:
                try:
                    vector_store = self.load_index(name, embeddings)

                    # 尝试执行搜索以验证索引可用性
                    if hasattr(vector_store, "similarity_search"):
                        results = vector_store.similarity_search("test query", k=1)
                        # 搜索成功，索引可用
                        health_report["info"]["search_test"] = "passed"

                except Exception as e:
                    health_report["healthy"] = False
                    health_report["issues"].append(f"索引加载或搜索失败: {str(e)}")
                    health_report["recommendations"].append("考虑使用 rebuild_index 重建索引")

            # 检查索引大小
            try:
                total_size = sum(
                    f.stat().st_size
                    for f in index_path.rglob("*")
                    if f.is_file()
                )
                health_report["info"]["size_bytes"] = total_size
                health_report["info"]["size_mb"] = round(total_size / 1024 / 1024, 2)

                # 如果索引很大但没有文档，可能有问题
                if total_size > 100 * 1024 * 1024:  # > 100MB
                    num_docs = metadata.get("num_documents", 0) if metadata else 0
                    if num_docs < 100:
                        health_report["warnings"].append(
                            f"索引文件较大 ({health_report['info']['size_mb']} MB) "
                            f"但文档数量较少 ({num_docs})"
                        )
                        health_report["recommendations"].append("考虑重建索引以优化存储")

            except Exception as e:
                health_report["warnings"].append(f"无法计算索引大小: {str(e)}")

            # 检查版本历史
            versions = self.get_index_versions(name)
            if versions:
                health_report["info"]["num_versions"] = len(versions)
                last_version = versions[-1]
                health_report["info"]["last_version"] = last_version.get("version", "N/A")

            # 总体评估
            if not health_report["issues"]:
                health_report["healthy"] = True

            return health_report

        except Exception as e:
            health_report["healthy"] = False
            health_report["issues"].append(f"健康检查失败: {str(e)}")
            health_report["recommendations"].append("检查索引文件系统权限")
            return health_report

    def get_health_summary(self) -> Dict[str, Any]:
        """获取所有索引的健康摘要

        Returns:
            Dict[str, Any]: 健康摘要，包含:
                - total_indexes (int): 索引总数
                - healthy_indexes (int): 健康索引数
                - unhealthy_indexes (int): 不健康索引数
                - indexes (List[Dict[str, Any]]): 各索引的健康状态
        """
        indexes = self.list_indexes()

        summary = {
            "total_indexes": len(indexes),
            "healthy_indexes": 0,
            "unhealthy_indexes": 0,
            "indexes": [],
        }

        for index_info in indexes:
            name = index_info.get("name")
            if name:
                health = self.check_index_health(name)
                summary["indexes"].append({
                    "name": name,
                    "healthy": health["healthy"],
                    "issues": len(health["issues"]),
                    "warnings": len(health["warnings"]),
                })

                if health["healthy"]:
                    summary["healthy_indexes"] += 1
                else:
                    summary["unhealthy_indexes"] += 1

        return summary