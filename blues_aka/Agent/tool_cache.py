"""工具缓存装饰器模块

该模块提供了工具调用的缓存装饰器和辅助功能，
避免重复调用相同的工具，提高性能和节省 API 成本。

主要功能:
    - cached_tool: 工具缓存装饰器
    - ToolCacheManager: 缓存管理器
    - RedisBackend: Redis 缓存后端（可选）

Author: Blues AKA Team
"""

import logging
import functools
import hashlib
import json
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ToolCacheManager:
    """
    工具缓存管理器

    管理工具调用的缓存，支持内存和 Redis 后端。

    使用示例:
        >>> from blues_aka.Agent.tool_cache import ToolCacheManager
        >>>
        >>> cache_manager = ToolCacheManager(ttl_minutes=30)
        >>>
        >>> # 检查缓存
        >>> result = cache_manager.get("search", {"query": "机器学习"})
        >>> if result:
        >>>     return result
        >>>
        >>> # 设置缓存
        >>> cache_manager.set("search", {"query": "机器学习"}, search_result)
    """

    def __init__(
        self,
        ttl_minutes: int = 30,
        backend: str = "memory",
        redis_url: Optional[str] = None
    ):
        """
        初始化工具缓存管理器

        Args:
            ttl_minutes: 缓存过期时间（分钟）
                - 默认 30 分钟
            backend: 缓存后端类型
                - "memory": 内存缓存（默认）
                - "redis": Redis 缓存
            redis_url: Redis 连接 URL
                - 仅当 backend="redis" 时需要
                - 格式: redis://localhost:6379/0
        """
        self.ttl = timedelta(minutes=ttl_minutes)
        self.backend = backend

        if backend == "memory":
            self.cache: Dict[str, tuple[Any, datetime]] = {}
            logger.info(f"工具缓存管理器初始化: 内存后端, TTL={ttl_minutes}分钟")

        elif backend == "redis":
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info(f"工具缓存管理器初始化: Redis后端, TTL={ttl_minutes}分钟")
            except ImportError:
                logger.warning("redis 未安装，回退到内存缓存")
                self.backend = "memory"
                self.cache = {}
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}，回退到内存缓存")
                self.backend = "memory"
                self.cache = {}

        # 统计信息
        self.hits = 0
        self.misses = 0

    def _make_key(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        生成缓存键

        基于 tool_name 和 tool_input 生成唯一的缓存键。

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            str: MD5 哈希值
        """
        # 序列化输入参数（排序键以确保一致性）
        key_data = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[Any]:
        """
        获取缓存结果

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            Optional[Any]: 缓存的结果，如果未命中或过期返回 None
        """
        key = self._make_key(tool_name, tool_input)

        if self.backend == "memory":
            if key in self.cache:
                cached_data, timestamp = self.cache[key]

                # 检查是否过期
                if datetime.now() - timestamp < self.ttl:
                    self.hits += 1
                    logger.debug(f"缓存命中: {tool_name}")
                    return cached_data
                else:
                    # 过期，删除
                    del self.cache[key]
                    logger.debug(f"缓存过期: {tool_name}")

        elif self.backend == "redis":
            try:
                # 检查 Redis 中是否有缓存
                cached_data = self.redis_client.get(key)
                if cached_data:
                    self.hits += 1
                    logger.debug(f"Redis 缓存命中: {tool_name}")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")

        self.misses += 1
        return None

    def set(self, tool_name: str, tool_input: Dict[str, Any], result: Any):
        """
        设置缓存

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            result: 工具调用结果
        """
        key = self._make_key(tool_name, tool_input)

        if self.backend == "memory":
            self.cache[key] = (result, datetime.now())
            logger.debug(f"缓存保存: {tool_name}, 总计: {len(self.cache)}")

        elif self.backend == "redis":
            try:
                # 序列化并保存到 Redis
                # 设置过期时间（秒）
                ttl_seconds = int(self.ttl.total_seconds())
                self.redis_client.setex(
                    key,
                    ttl_seconds,
                    json.dumps(result, ensure_ascii=False)
                )
                logger.debug(f"Redis 缓存保存: {tool_name}")
            except Exception as e:
                logger.warning(f"Redis 保存失败: {e}")

    def clear(self):
        """清除所有缓存"""
        if self.backend == "memory":
            self.cache.clear()
        elif self.backend == "redis":
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis 清除失败: {e}")

        self.hits = 0
        self.misses = 0
        logger.info("工具缓存已清除")

    def cleanup_expired(self):
        """清理过期的缓存（仅内存后端）"""
        if self.backend == "memory":
            current_time = datetime.now()
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp >= self.ttl
            ]

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.info(f"清理过期缓存: {len(expired_keys)} 个")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
                - total_calls: 总调用次数
                - hits: 缓存命中次数
                - misses: 缓存未命中次数
                - hit_rate: 命中率（0-1）
                - cache_size: 当前缓存大小
                - backend: 缓存后端类型
        """
        total_calls = self.hits + self.misses
        cache_size = len(self.cache) if self.backend == "memory" else "未知"

        return {
            "total_calls": total_calls,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total_calls if total_calls > 0 else 0.0,
            "cache_size": cache_size,
            "backend": self.backend
        }


def cached_tool(
    cache_manager: Optional[ToolCacheManager] = None,
    ttl_minutes: int = 30
):
    """
    工具缓存装饰器

    自动为工具函数添加缓存功能，避免重复调用。

    Args:
        cache_manager: 缓存管理器实例
            - None: 自动创建默认管理器
            - ToolCacheManager: 自定义管理器
        ttl_minutes: 缓存过期时间（分钟）
            - 仅当 cache_manager=None 时使用
            - 默认 30 分钟

    Returns:
        装饰器函数

    使用示例:
        >>> from blues_aka.Agent.tool_cache import cached_tool
        >>>
        >>> @cached_tool(ttl_minutes=60)
        >>> def expensive_search(query: str) -> str:
        >>>     # 昂贵的搜索操作
        >>>     return search_api(query)
        >>>
        >>> # 第一次调用 - 执行搜索
        >>> result1 = expensive_search("机器学习")
        >>>
        >>> # 第二次调用 - 使用缓存
        >>> result2 = expensive_search("机器学习")  # 瞬间返回
        >>>
        >>> # 查看缓存统计
        >>> print(expensive_search.cache_stats)
    """
    def decorator(func: Callable) -> Callable:
        # 创建或使用缓存管理器
        nonlocal cache_manager
        if cache_manager is None:
            cache_manager = ToolCacheManager(ttl_minutes=ttl_minutes)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 构建缓存键
            tool_name = func.__name__
            tool_input = {"args": args, "kwargs": kwargs}

            # 尝试从缓存获取
            cached_result = cache_manager.get(tool_name, tool_input)
            if cached_result is not None:
                logger.info(f"缓存命中: {tool_name}")
                return cached_result

            # 调用原始函数
            logger.info(f"调用工具: {tool_name}")
            result = func(*args, **kwargs)

            # 保存到缓存
            cache_manager.set(tool_name, tool_input, result)

            return result

        # 添加缓存统计方法
        def get_cache_stats() -> Dict[str, Any]:
            return cache_manager.get_stats()

        def clear_cache():
            cache_manager.clear()

        def get_cache_manager() -> ToolCacheManager:
            return cache_manager

        # 附加方法到包装函数
        wrapper.cache_stats = get_cache_stats
        wrapper.clear_cache = clear_cache
        wrapper.cache_manager = get_cache_manager

        return wrapper

    return decorator


class CachedTool:
    """
    缓存工具类

    用于创建带缓存功能的工具实例。

    使用示例:
        >>> from blues_aka.Agent.tool_cache import CachedTool
        >>>
        >>> @CachedTool(ttl_minutes=30)
        >>> def my_tool(query: str) -> str:
        >>>     return expensive_operation(query)
        >>>
        >>> # 使用工具
        >>> result1 = my_tool("test")
        >>> result2 = my_tool("test")  # 使用缓存
        >>>
        >>> # 查看统计
        >>> print(my_tool.get_cache_stats())
    """

    def __init__(
        self,
        func: Callable,
        ttl_minutes: int = 30,
        backend: str = "memory",
        redis_url: Optional[str] = None
    ):
        """
        初始化缓存工具

        Args:
            func: 工具函数
            ttl_minutes: 缓存过期时间（分钟）
            backend: 缓存后端类型
            redis_url: Redis 连接 URL
        """
        self.func = func
        self.cache_manager = ToolCacheManager(
            ttl_minutes=ttl_minutes,
            backend=backend,
            redis_url=redis_url
        )
        self.ttl_minutes = ttl_minutes

        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        """调用工具（带缓存）"""
        # 构建缓存键
        tool_name = self.func.__name__
        tool_input = {"args": args, "kwargs": kwargs}

        # 尝试从缓存获取
        cached_result = self.cache_manager.get(tool_name, tool_input)
        if cached_result is not None:
            logger.info(f"缓存命中: {tool_name}")
            return cached_result

        # 调用原始函数
        logger.info(f"调用工具: {tool_name}")
        result = self.func(*args, **kwargs)

        # 保存到缓存
        self.cache_manager.set(tool_name, tool_input, result)

        return result

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.cache_manager.get_stats()

    def clear_cache(self):
        """清除缓存"""
        self.cache_manager.clear()

    def __repr__(self):
        return f"CachedTool({self.func.__name__}, ttl={self.ttl_minutes}min)"


# 创建全局默认缓存管理器
_default_cache_manager = None


def get_default_cache_manager() -> ToolCacheManager:
    """
    获取全局默认缓存管理器

    Returns:
        ToolCacheManager: 默认缓存管理器实例
    """
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = ToolCacheManager()
    return _default_cache_manager


def cache_tool_result(
    tool_name: str,
    tool_input: Dict[str, Any],
    result: Any,
    ttl_minutes: Optional[int] = None
):
    """
    缓存工具结果的便捷函数

    Args:
        tool_name: 工具名称
        tool_input: 工具输入参数
        result: 工具调用结果
        ttl_minutes: 缓存过期时间（分钟）
            - None: 使用默认 TTL
            - 默认 None

    使用示例:
        >>> from blues_aka.Agent.tool_cache import cache_tool_result
        >>>
        >>> # 手动缓存工具结果
        >>> result = search_api("机器学习")
        >>> cache_tool_result("search", {"query": "机器学习"}, result)
        >>>
        >>> # 稍后获取缓存
        >>> from blues_aka.Agent.tool_cache import get_default_cache_manager
        >>> cache = get_default_cache_manager()
        >>> cached = cache.get("search", {"query": "机器学习"})
    """
    cache_manager = get_default_cache_manager()
    cache_manager.set(tool_name, tool_input, result)
    logger.debug(f"工具结果已缓存: {tool_name}")


def get_cached_tool_result(
    tool_name: str,
    tool_input: Dict[str, Any]
) -> Optional[Any]:
    """
    获取缓存的工具结果

    Args:
        tool_name: 工具名称
        tool_input: 工具输入参数

    Returns:
        Optional[Any]: 缓存的结果，如果未命中返回 None

    使用示例:
        >>> from blues_aka.Agent.tool_cache import get_cached_tool_result
        >>>
        >>> # 尝试从缓存获取
        >>> result = get_cached_tool_result("search", {"query": "机器学习"})
        >>> if result:
        >>>     print("使用缓存结果")
        >>> else:
        >>>     result = search_api("机器学习")
    """
    cache_manager = get_default_cache_manager()
    return cache_manager.get(tool_name, tool_input)
