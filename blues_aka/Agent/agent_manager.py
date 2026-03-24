"""Agent管理器模块

该模块提供了Agent实例的管理和复用功能，避免重复创建Agent实例，
提高性能和资源利用率。

主要功能:
    - AgentManager: Agent实例管理器（单例模式）
    - 配置缓存和复用
    - 生命周期管理
    - 统计和监控

Author: Blues AKA Team
"""

import logging
import hashlib
import json
import threading
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from blues_aka.Agent.BaseAgent import BaseAgent

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Agent实例管理器

    负责创建、缓存和复用Agent实例，避免重复创建带来的性能开销。

    主要特性:
        1. 单例模式: 全局唯一的Agent管理器
        2. 配置哈希: 基于配置生成唯一键，相同配置复用实例
        3. 生命周期管理: 支持过期清理和手动清理
        4. 线程安全: 使用锁保证并发安全
        5. 统计监控: 记录缓存命中率和创建次数

    使用示例:
        >>> from blues_aka.Agent.agent_manager import AgentManager
        >>>
        >>> # 获取管理器实例
        >>> manager = AgentManager.get_instance()
        >>>
        >>> # 获取或创建Agent
        >>> agent_config = {
        ...     'model': 'glm-4.5',
        ...     'enable_rag': True,
        ...     'rag_index_name': 'my_kb'
        ... }
        >>> agent = manager.get_or_create_agent(agent_config)
        >>>
        >>> # 后续相同配置会复用实例
        >>> agent2 = manager.get_or_create_agent(agent_config)  # 复用
        >>>
        >>> # 查看统计
        >>> stats = manager.get_stats()
        >>> print(f"缓存命中率: {stats['hit_rate']:.2%}")
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化Agent管理器

        注意: 由于单例模式，此方法只会被调用一次
        """
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        self._agents: Dict[str, tuple[BaseAgent, datetime]] = {}
        self._config_keys: Dict[str, str] = {}  # agent_id -> config_key
        self._creation_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._max_cache_size = 100  # 最大缓存数量
        self._cache_ttl_minutes = 60  # 缓存过期时间（分钟）
        self._lock = threading.RLock()  # 可重入锁

        logger.info("Agent管理器初始化完成")

    def get_or_create_agent(
        self,
        agent_config: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> BaseAgent:
        """
        获取或创建Agent实例

        如果配置相同，返回缓存的实例；否则创建新实例并缓存。

        Args:
            agent_config: Agent配置字典
                - model: 模型名称或实例
                - tools: 工具列表
                - system_prompt: 系统提示词
                - enable_rag: 是否启用RAG
                - rag_index_name: RAG索引名称
                - rag_config: RAG配置
                - enable_thinking: 是否启用深度思考
                - enable_tool_cache: 是否启用工具缓存
                - 等等...
            agent_id: 可选的Agent标识符
                - 如果提供，会优先通过agent_id查找
                - 如果未提供，则通过配置哈希查找

        Returns:
            BaseAgent: Agent实例

        Raises:
            Exception: Agent创建失败时抛出异常

        示例:
            >>> manager = AgentManager.get_instance()
            >>>
            >>> # 使用agent_id复用
            >>> agent = manager.get_or_create_agent(
            ...     agent_config={'model': 'glm-4.5'},
            ...     agent_id='my_agent'
            ... )
            >>>
            >>> # 仅通过配置复用
            >>> agent = manager.get_or_create_agent({
            ...     'model': 'glm-4.5',
            ...     'enable_rag': True
            ... })
        """
        # 生成配置键
        config_key = self._make_config_key(agent_config)

        with self._lock:
            # 方案1: 如果提供了agent_id，先尝试通过agent_id查找
            if agent_id:
                if agent_id in self._config_keys:
                    cached_key = self._config_keys[agent_id]
                    if cached_key in self._agents:
                        agent, created_at = self._agents[cached_key]

                        # 检查是否过期
                        if self._is_cache_valid(created_at):
                            self._cache_hits += 1
                            logger.info(f"复用Agent实例 (agent_id={agent_id})")
                            return agent
                        else:
                            # 过期，删除
                            del self._agents[cached_key]
                            del self._config_keys[agent_id]

            # 方案2: 通过配置键查找
            if config_key in self._agents:
                agent, created_at = self._agents[config_key]

                # 检查是否过期
                if self._is_cache_valid(created_at):
                    self._cache_hits += 1
                    logger.info(f"复用Agent实例 (config_key={config_key[:8]}...)")

                    # 如果提供了agent_id，建立映射
                    if agent_id:
                        self._config_keys[agent_id] = config_key

                    return agent
                else:
                    # 过期，删除
                    del self._agents[config_key]

            # 缓存未命中，创建新实例
            self._cache_misses += 1
            logger.info(f"创建新的Agent实例 (config_key={config_key[:8]}...)")

            try:
                agent = BaseAgent(**agent_config)
                self._creation_count += 1

                # 缓存实例
                self._agents[config_key] = (agent, datetime.now())

                # 如果提供了agent_id，建立映射
                if agent_id:
                    self._config_keys[agent_id] = config_key

                # 检查缓存大小，清理最旧的实例
                self._cleanup_cache_if_needed()

                logger.info(f"Agent实例创建成功并已缓存 (总数: {len(self._agents)})")
                return agent

            except Exception as e:
                logger.error(f"创建Agent实例失败: {e}", exc_info=True)
                raise

    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        """
        通过agent_id获取Agent实例

        Args:
            agent_id: Agent标识符

        Returns:
            Optional[BaseAgent]: Agent实例，如果未找到返回None
        """
        with self._lock:
            if agent_id not in self._config_keys:
                return None

            config_key = self._config_keys[agent_id]

            if config_key not in self._agents:
                return None

            agent, created_at = self._agents[config_key]

            # 检查是否过期
            if not self._is_cache_valid(created_at):
                del self._agents[config_key]
                del self._config_keys[agent_id]
                return None

            return agent

    def remove_agent(self, agent_id: Optional[str] = None, agent_config: Optional[Dict[str, Any]] = None):
        """
        移除缓存的Agent实例

        Args:
            agent_id: Agent标识符（优先）
            agent_config: Agent配置（如果agent_id未提供）

        注意:
            - 如果提供了agent_id，优先使用agent_id删除
            - 如果只提供了agent_config，则通过配置哈希删除
            - 如果两者都提供了，优先使用agent_id
        """
        with self._lock:
            if agent_id:
                # 通过agent_id删除
                if agent_id in self._config_keys:
                    config_key = self._config_keys[agent_id]
                    del self._config_keys[agent_id]

                    if config_key in self._agents:
                        del self._agents[config_key]
                        logger.info(f"已移除Agent实例 (agent_id={agent_id})")
            elif agent_config:
                # 通过配置删除
                config_key = self._make_config_key(agent_config)
                if config_key in self._agents:
                    del self._agents[config_key]

                    # 删除所有映射到此配置的agent_id
                    to_delete = [
                        aid for aid, key in self._config_keys.items()
                        if key == config_key
                    ]
                    for aid in to_delete:
                        del self._config_keys[aid]

                    logger.info(f"已移除Agent实例 (config_key={config_key[:8]}...)")

    def clear_cache(self):
        """清除所有缓存的Agent实例"""
        with self._lock:
            count = len(self._agents)
            self._agents.clear()
            self._config_keys.clear()
            logger.info(f"已清除所有Agent缓存 (数量: {count})")

    def cleanup_expired(self):
        """清理过期的Agent实例"""
        with self._lock:
            expired_keys = []

            for config_key, (_, created_at) in self._agents.items():
                if not self._is_cache_valid(created_at):
                    expired_keys.append(config_key)

            for config_key in expired_keys:
                del self._agents[config_key]

                # 删除映射
                to_delete = [
                    aid for aid, key in self._config_keys.items()
                    if key == config_key
                ]
                for aid in to_delete:
                    del self._config_keys[aid]

            if expired_keys:
                logger.info(f"清理过期Agent实例: {len(expired_keys)} 个")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取管理器统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
                - total_agents: 当前缓存的Agent数量
                - creation_count: 总创建次数
                - cache_hits: 缓存命中次数
                - cache_misses: 缓存未命中次数
                - hit_rate: 缓存命中率（0-1）
                - max_cache_size: 最大缓存大小
                - cache_ttl_minutes: 缓存过期时间（分钟）
        """
        total_requests = self._cache_hits + self._cache_misses

        return {
            "total_agents": len(self._agents),
            "creation_count": self._creation_count,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": self._cache_hits / total_requests if total_requests > 0 else 0.0,
            "max_cache_size": self._max_cache_size,
            "cache_ttl_minutes": self._cache_ttl_minutes
        }

    def get_cached_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有缓存的Agent配置

        Returns:
            List[Dict[str, Any]]: 配置列表（不包含敏感信息）
        """
        with self._lock:
            configs = []
            for config_key, (agent, _) in self._agents.items():
                config_info = {
                    "config_key": config_key,
                    "model": str(agent.model),
                    "enable_rag": agent.enable_rag,
                    "rag_index_name": agent.rag_index_name if agent.enable_rag else None,
                    "enable_thinking": agent.enable_thinking
                }
                configs.append(config_info)
            return configs

    def set_max_cache_size(self, size: int):
        """
        设置最大缓存大小

        Args:
            size: 最大缓存数量
        """
        with self._lock:
            old_size = self._max_cache_size
            self._max_cache_size = size
            logger.info(f"最大缓存大小已更新: {old_size} -> {size}")

            # 清理超出的缓存
            self._cleanup_cache_if_needed()

    def set_cache_ttl(self, minutes: int):
        """
        设置缓存过期时间

        Args:
            minutes: 过期时间（分钟）
        """
        with self._lock:
            old_ttl = self._cache_ttl_minutes
            self._cache_ttl_minutes = minutes
            logger.info(f"缓存TTL已更新: {old_ttl} -> {minutes} 分钟")

    def _make_config_key(self, config: Dict[str, Any]) -> str:
        """
        生成配置的唯一键

        Args:
            config: Agent配置字典

        Returns:
            str: MD5哈希值
        """
        # 深拷贝配置，避免修改原始配置
        config_copy = config.copy()

        # 处理特殊字段
        # 1. tools: 工具列表需要序列化
        if 'tools' in config_copy and config_copy['tools'] is not None:
            tools = config_copy['tools']
            if isinstance(tools, list):
                # 提取工具名称列表
                tool_names = [getattr(tool, 'name', str(tool)) for tool in tools]
                config_copy['tools'] = sorted(tool_names)
            else:
                config_copy['tools'] = str(tools)

        # 2. model: 模型需要转换为字符串
        if 'model' in config_copy:
            model = config_copy['model']
            if hasattr(model, 'model_name'):
                config_copy['model'] = model.model_name
            else:
                config_copy['model'] = str(model)

        # 3. rag_config: JSON序列化并排序
        if 'rag_config' in config_copy and config_copy['rag_config']:
            if isinstance(config_copy['rag_config'], dict):
                config_copy['rag_config'] = json.dumps(
                    config_copy['rag_config'],
                    sort_keys=True
                )
            elif isinstance(config_copy['rag_config'], str):
                # 已经是字符串，尝试解析并重新序列化以确保一致性
                try:
                    parsed = json.loads(config_copy['rag_config'])
                    config_copy['rag_config'] = json.dumps(parsed, sort_keys=True)
                except:
                    pass  # 保持原样

        # 序列化并排序
        sorted_config = json.dumps(config_copy, sort_keys=True)

        # 生成MD5哈希
        return hashlib.md5(sorted_config.encode('utf-8')).hexdigest()

    def _is_cache_valid(self, created_at: datetime) -> bool:
        """
        检查缓存是否有效

        Args:
            created_at: 创建时间

        Returns:
            bool: True表示有效，False表示过期
        """
        ttl = timedelta(minutes=self._cache_ttl_minutes)
        return datetime.now() - created_at < ttl

    def _cleanup_cache_if_needed(self):
        """如果缓存超出限制，清理最旧的实例"""
        if len(self._agents) <= self._max_cache_size:
            return

        # 按创建时间排序
        sorted_items = sorted(
            self._agents.items(),
            key=lambda x: x[1][1]  # 按创建时间排序
        )

        # 删除最旧的实例
        num_to_delete = len(self._agents) - self._max_cache_size
        for config_key, _ in sorted_items[:num_to_delete]:
            del self._agents[config_key]

            # 删除映射
            to_delete = [
                aid for aid, key in self._config_keys.items()
                if key == config_key
            ]
            for aid in to_delete:
                del self._config_keys[aid]

        logger.info(f"缓存清理完成，删除了 {num_to_delete} 个最旧的实例")

    @classmethod
    def get_instance(cls) -> 'AgentManager':
        """
        获取AgentManager单例实例

        Returns:
            AgentManager: 全局唯一的Agent管理器实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        with cls._lock:
            cls._instance = None
        logger.info("AgentManager实例已重置")


# 全局便捷函数
def get_agent_manager() -> AgentManager:
    """
    获取全局Agent管理器实例

    Returns:
        AgentManager: Agent管理器实例
    """
    return AgentManager.get_instance()


def get_or_create_agent(agent_config: Dict[str, Any], agent_id: Optional[str] = None) -> BaseAgent:
    """
    获取或创建Agent实例（便捷函数）

    Args:
        agent_config: Agent配置字典
        agent_id: 可选的Agent标识符

    Returns:
        BaseAgent: Agent实例

    示例:
        >>> from blues_aka.Agent.agent_manager import get_or_create_agent
        >>>
        >>> agent = get_or_create_agent({
        ...     'model': 'glm-4.5',
        ...     'enable_rag': True
        ... })
    """
    manager = get_agent_manager()
    return manager.get_or_create_agent(agent_config, agent_id)
