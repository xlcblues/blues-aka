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
    """索引管理器"""

    def __init__(self, base_path: Optional[str] = None):
        """初始化索引管理器"""
        from blues_aka import ConfigFactory
        _config = ConfigFactory.get_config()

        self.base_path = Path(base_path or _config.vector_store_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"索引管理器初始化: {self.base_path}")

    def _get_index_path(self, name: str) -> Path:
        """获取索引的完整路径"""
        return self.base_path / name

    def _get_metadata_path(self, name: str) -> Path:
        """获取索引元数据文件路径"""
        return self._get_index_path(name) / "metadata.json"

    def _save_metadata(
            self,
            name: str,
            metadata: Dict[str, Any],
    ) -> None:
        """保存索引元数据"""
        metadata_path = self._get_metadata_path(name)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.debug(f"保存元数据: {metadata_path}")

    def _load_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """加载索引元数据"""
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
        """创建新索引"""
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
        """加载索引"""
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
        """更新索引（添加新文档）"""
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
        """删除索引"""
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
        """列出所有索引"""
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
        """获取索引详细信息"""
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
        """检查索引是否存在"""
        return self._get_index_path(name).exists()