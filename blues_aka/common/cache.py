"""
缓存工具模块

提供统一的缓存接口，支持Redis和内存缓存两种方式。
主要用于缓存频繁访问但不常变化的数据，以提高系统性能。

主要功能:
    - 统一的缓存接口
    - 支持Redis和内存缓存
    - 缓存装饰器
    - 自动缓存失效

使用示例:
    # 基本使用
    from blues_aka.common.cache import cache_manager

    # 设置缓存
    cache_manager.set('user:123', user_data, timeout=300)

    # 获取缓存
    user_data = cache_manager.get('user:123')

    # 删除缓存
    cache_manager.delete('user:123')

    # 使用装饰器
    @cache_manager.cached(timeout=300, key_prefix='user_list')
    def get_user_list():
        return User.query.all()
"""

import hashlib
import json
import logging
import pickle
import time
from functools import wraps
from typing import Any, Callable, Optional, Union

# 尝试导入Redis，如果不可用则使用内存缓存
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheBackend:
    """缓存后端基类"""

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """设置缓存"""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """删除缓存"""
        raise NotImplementedError

    def clear(self) -> bool:
        """清空所有缓存"""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端（用于开发环境或Redis不可用时）"""

    def __init__(self):
        self._cache = {}
        self._expires = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            # 检查是否过期
            if key in self._expires:
                if time.time() > self._expires[key]:
                    # 已过期，删除
                    del self._cache[key]
                    del self._expires[key]
                    return None
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """设置缓存"""
        self._cache[key] = value
        if timeout:
            self._expires[key] = time.time() + timeout
        return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            if key in self._expires:
                del self._expires[key]
            return True
        return False

    def clear(self) -> bool:
        """清空所有缓存"""
        self._cache.clear()
        self._expires.clear()
        return True

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._cache


class RedisCacheBackend(CacheBackend):
    """Redis缓存后端"""

    def __init__(self, redis_client):
        """
        初始化Redis缓存后端

        Args:
            redis_client: Redis客户端实例
        """
        self.client = redis_client

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.client.get(key)
            if value is not None:
                # 尝试反序列化
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, EOFError):
                    # 如果反序列化失败，返回原始值
                    return value.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Redis获取缓存失败: {key}, 错误: {e}")
            return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            # 序列化值
            serialized_value = pickle.dumps(value)
            if timeout:
                return self.client.setex(key, timeout, serialized_value)
            else:
                return self.client.set(key, serialized_value)
        except Exception as e:
            logger.error(f"Redis设置缓存失败: {key}, 错误: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis删除缓存失败: {key}, 错误: {e}")
            return False

    def clear(self) -> bool:
        """清空所有缓存（仅删除带前缀的键）"""
        try:
            # 注意：这里只删除带我们前缀的键，避免删除其他数据
            keys = self.client.keys('cache:*')
            if keys:
                return self.client.delete(*keys) > 0
            return True
        except Exception as e:
            logger.error(f"Redis清空缓存失败: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis检查键是否存在失败: {key}, 错误: {e}")
            return False


class CacheManager:
    """缓存管理器"""

    def __init__(self, backend: CacheBackend, prefix: str = 'cache'):
        """
        初始化缓存管理器

        Args:
            backend: 缓存后端实例
            prefix: 缓存键前缀
        """
        self.backend = backend
        self.prefix = prefix
        logger.info(f"缓存管理器初始化完成，后端类型: {type(backend).__name__}")

    def _make_key(self, key: str) -> str:
        """生成完整的缓存键"""
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在则返回None
        """
        full_key = self._make_key(key)
        value = self.backend.get(full_key)
        if value is not None:
            logger.debug(f"缓存命中: {key}")
        else:
            logger.debug(f"缓存未命中: {key}")
        return value

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒），None表示永不过期

        Returns:
            是否设置成功
        """
        full_key = self._make_key(key)
        result = self.backend.set(full_key, value, timeout)
        if result:
            logger.debug(f"缓存设置成功: {key}, 过期时间: {timeout}")
        else:
            logger.warning(f"缓存设置失败: {key}")
        return result

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        full_key = self._make_key(key)
        result = self.backend.delete(full_key)
        if result:
            logger.debug(f"缓存删除成功: {key}")
        return result

    def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否清空成功
        """
        return self.backend.clear()

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            缓存是否存在
        """
        full_key = self._make_key(key)
        return self.backend.exists(full_key)

    def cached(self, timeout: int = 300, key_prefix: str = '', cache_user_specific: bool = False):
        """
        缓存装饰器

        Args:
            timeout: 缓存过期时间（秒）
            key_prefix: 缓存键前缀
            cache_user_specific: 是否根据用户ID区分缓存

        Returns:
            装饰器函数

        Example:
            @cache_manager.cached(timeout=600, key_prefix='user_list')
            def get_users():
                return User.query.all()

            @cache_manager.cached(timeout=300, key_prefix='user_detail', cache_user_specific=True)
            def get_current_user(user_id):
                return User.query.get(user_id)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                # 1. 添加函数名
                cache_key_parts = [func.__name__]

                # 2. 添加自定义前缀
                if key_prefix:
                    cache_key_parts.insert(0, key_prefix)

                # 3. 如果需要根据用户ID区分，从kwargs中获取user_id
                if cache_user_specific:
                    user_id = kwargs.get('user_id') or kwargs.get('id')
                    if user_id:
                        cache_key_parts.append(f'user_{user_id}')

                # 4. 添加参数的hash值
                if args or kwargs:
                    # 创建参数的稳定表示
                    params_dict = {}
                    for i, arg in enumerate(args):
                        params_dict[f'arg_{i}'] = str(arg)
                    for k, v in sorted(kwargs.items()):
                        if k != 'user_id' and k != 'id':  # 避免重复添加
                            params_dict[k] = str(v)

                    params_str = json.dumps(params_dict, sort_keys=True)
                    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                    cache_key_parts.append(params_hash)

                cache_key = ':'.join(cache_key_parts)

                # 尝试从缓存获取
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                result = func(*args, **kwargs)

                # 存入缓存
                self.set(cache_key, result, timeout=timeout)

                return result

            return wrapper
        return decorator

    def invalidate_pattern(self, pattern: str):
        """
        使匹配模式的所有缓存失效

        Args:
            pattern: 缓存键模式（支持通配符*）
        """
        try:
            if isinstance(self.backend, RedisCacheBackend):
                # Redis支持模式匹配
                full_pattern = self._make_key(pattern).replace('*', '*')
                keys = self.backend.client.keys(full_pattern)
                if keys:
                    self.backend.client.delete(*keys)
                    logger.info(f"清空匹配模式的缓存: {pattern}, 删除了 {len(keys)} 个键")
            else:
                # 内存缓存只支持简单的模式匹配
                full_prefix = self._make_key(pattern.replace('*', ''))
                if hasattr(self.backend, '_cache'):
                    keys_to_delete = [k for k in self.backend._cache.keys() if k.startswith(full_prefix)]
                    for key in keys_to_delete:
                        self.backend.delete(key)
                    logger.info(f"清空匹配模式的缓存: {pattern}, 删除了 {len(keys_to_delete)} 个键")
        except Exception as e:
            logger.error(f"清空缓存模式失败: {pattern}, 错误: {e}")


# 创建默认的缓存管理器实例
def create_cache_manager(config=None):
    """
    创建缓存管理器

    Args:
        config: 配置对象（支持字典式访问）

    Returns:
        CacheManager实例
    """
    # 尝试使用Redis
    if REDIS_AVAILABLE and config:
        try:
            # 获取Redis URL（支持字典式访问）
            redis_url = config.get('REDIS_URL') if hasattr(config, 'get') else config.REDIS_URL

            # 隐藏密码的Redis URL（用于日志显示）
            safe_url = redis_url
            if '://' in safe_url and '@' in safe_url:
                # 隐藏密码部分
                parts = safe_url.split('://')
                if len(parts) == 2:
                    auth_part, rest = parts[1].split('@', 1)
                    safe_url = f"{parts[0]}://****@{rest}"

            logger.info(f"尝试连接Redis: {safe_url}")

            redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # 我们自己处理序列化
                socket_timeout=5,
                socket_connect_timeout=5
            )

            # 测试连接
            redis_client.ping()
            backend = RedisCacheBackend(redis_client)
            logger.info(f"✅ Redis连接成功！使用Redis作为缓存后端")
        except Exception as e:
            logger.warning(f"❌ Redis连接失败，降级使用内存缓存: {e}")
            backend = MemoryCacheBackend()
    else:
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis未安装，使用内存缓存作为缓存后端")
        else:
            logger.warning("⚠️ Redis配置未找到，使用内存缓存作为缓存后端")
        backend = MemoryCacheBackend()

    return CacheManager(backend, prefix='blues_aka')


# 全局缓存管理器实例（延迟初始化）
cache_manager = None


def init_cache(app):
    """
    初始化缓存系统

    Args:
        app: Flask应用实例
    """
    global cache_manager
    cache_manager = create_cache_manager(app.config)
    app.cache = cache_manager
    logger.info("缓存系统初始化完成")


def get_cache() -> Optional[CacheManager]:
    """
    获取缓存管理器实例

    Returns:
        CacheManager实例，如果未初始化则返回None
    """
    return cache_manager
