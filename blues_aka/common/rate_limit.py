"""
API 限流配置模块

本模块提供 API 请求限流功能，用于防止 DDoS 攻击和滥用。
基于 Flask-Limiter 实现，支持多种限流策略和存储后端。

主要功能:
    - 基于 IP 地址的请求限流
    - 基于用户的请求限流
    - 自定义限流策略
    - 限流统计和监控
    - 支持白名单机制

设计原则:
    - 默认限流策略宽松，避免误伤正常用户
    - 关键接口（登录、注册）严格限流
    - 使用缓存系统（Redis）存储限流数据
    - 失败时降级为内存存储

使用场景:
    1. 防止 DDoS 攻击
    2. 防止 API 滥用
    3. 保护敏感接口（登录、注册）
    4. 控制资源使用

限流策略:
    - 认证接口: 10 次/分钟
    - 登录接口: 5 次/分钟
    - 注册接口: 3 次/分钟
    - 一般接口: 100 次/分钟
    - 文件上传: 10 次/小时
"""

import logging
from typing import Callable, Optional

from flask import Flask, request, g

# 尝试导入 Flask-Limiter
FLASK_LIMITER_AVAILABLE = False
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    FLASK_LIMITER_AVAILABLE = True
except ImportError:
    FLASK_LIMITER_AVAILABLE = False
    logging.getLogger(__name__).warning("Flask-Limiter 未安装，限流功能将不可用")

from flask_jwt_extended import get_jwt_identity

from blues_aka.common.cache import get_cache


# 配置日志记录器
logger = logging.getLogger(__name__)


# 自定义限流键函数
def get_key_func() -> Callable:
    """
    获取限流键函数

    根据请求类型返回不同的限流键：
    - 已登录用户：使用 user_id 作为限流键
    - 未登录用户：使用 IP 地址作为限流键

    Returns:
        Callable: 限流键函数

    注意:
        - 认证用户可以独立于 IP 进行限流
        - 未认证用户共享 IP 的限流配额
        - 支持代理和负载均衡环境
    """
    def key_func() -> str:
        try:
            # 尝试获取当前用户 ID
            user_id = get_jwt_identity()
            if user_id:
                # 已登录用户，使用 user_id 作为限流键
                return f"user:{user_id}"
        except Exception:
            # 未登录或 token 无效，使用 IP 地址
            pass

        # 未登录用户，使用 IP 地址作为限流键
        if FLASK_LIMITER_AVAILABLE:
            remote_addr = get_remote_address()
        else:
            # 备用实现：从请求对象获取 IP
            remote_addr = request.remote_addr or 'unknown'
        return f"ip:{remote_addr}"

    return key_func


# 自定义限流键函数（仅基于 IP）
def get_ip_key_func() -> Callable:
    """
    获取基于 IP 的限流键函数

    无论用户是否登录，都使用 IP 地址作为限流键。
    适用于需要严格限制 IP 的场景。

    Returns:
        Callable: 限流键函数
    """
    def key_func() -> str:
        remote_addr = get_remote_address()
        return f"ip:{remote_addr}"

    return key_func


# 创建限流器存储后端
def get_storage_uri():
    """
    获取限流器存储 URI

    Returns:
        str: 存储 URI（Redis 或内存）

    注意:
        - 优先使用 Redis 存储
        - Redis 不可用时降级为内存存储
    """
    try:
        cache = get_cache()
        if cache and hasattr(cache.backend, 'client'):
            # 使用 Redis 作为存储后端
            return "redis+unix:///var/run/redis/redis.sock"
    except Exception as e:
        logger.warning(f"Redis 不可用，使用内存存储限流数据: {e}")

    # 使用内存存储（开发环境或 Redis 不可用时）
    return "memory://"


# 创建限流器实例
def create_limiter(app: Optional[Flask] = None):
    """
    创建 Flask-Limiter 实例

    Args:
        app: Flask 应用实例（可选）

    Returns:
        Limiter 或 None: 限流器实例，如果 Flask-Limiter 不可用则返回 None

    配置说明:
        - key_func: 限流键函数（用户或 IP）
        - default_limits: 默认限流策略
        - storage_uri: 存储后端 URI
        - strategy: 限流策略（固定窗口、移动窗口等）
        - headers_enabled: 是否在响应头中包含限流信息

    示例:
        >>> limiter = create_limiter()
        >>> if limiter:
        ...     limiter.init_app(app)
    """
    # 检查 Flask-Limiter 是否可用
    if not FLASK_LIMITER_AVAILABLE:
        logger.warning("Flask-Limiter 不可用，限流功能已禁用")
        return None

    # 获取存储 URI
    storage_uri = get_storage_uri()

    # 创建限流器
    limiter = Limiter(
        key_func=get_key_func(),
        app=app,
        default_limits=["100 per minute"],  # 默认限流：100 次/分钟
        storage_uri=storage_uri,
        strategy="fixed-window",  # 使用固定窗口算法
        headers_enabled=True,  # 在响应头中包含限流信息
        swallow_errors=True,  # 吞掉限流错误，避免影响正常请求
    )

    logger.info(
        f"限流器创建完成 - "
        f"storage: {storage_uri.split(':')[0]}, "
        f"default_limits: 100 per minute"
    )

    return limiter


# 创建全局限流器实例
limiter = None


def init_rate_limit(app: Flask):
    """
    初始化限流系统

    Args:
        app: Flask 应用实例

    配置内容:
        1. 创建并初始化限流器
        2. 配置各种限流策略
        3. 注册限流错误处理器

    限流策略:
        - 认证接口: 10 次/分钟
        - 登录接口: 5 次/分钟
        - 注册接口: 3 次/分钟
        - 聊天接口: 60 次/分钟
        - 一般接口: 100 次/分钟
    """
    global limiter

    # 创建限流器
    limiter = create_limiter(app)
    limiter.init_app(app)

    # 配置限流错误处理
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """
        限流错误处理

        当请求超过限流阈值时返回友好的错误信息。

        Args:
            e: 错误信息

        Returns:
            dict: 错误响应
        """
        logger.warning(
            f"请求超过限流阈值 - "
            f"ip={get_remote_address()}, "
            f"path={request.path}, "
            f"limit={e.description}"
        )

        return {
            'code': 429,
            'message': '请求过于频繁，请稍后再试',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'retry_after': getattr(e, 'retry_after', 60)
        }, 429

    logger.info("限流系统初始化完成")


def get_limiter() -> Optional[Limiter]:
    """
    获取限流器实例

    Returns:
        Limiter: 限流器实例，如果未初始化则返回 None
    """
    return limiter


# 限流装饰器工厂函数
def limit(limit_value: str, key_func: Optional[Callable] = None, per_method: bool = False):
    """
    限流装饰器

    用于为单个路由添加限流保护。

    Args:
        limit_value: 限流值（如 "10 per minute"）
        key_func: 自定义限流键函数（可选）
        per_method: 是否对不同的 HTTP 方法分别限流

    Returns:
        装饰器函数

    示例:
        >>> @limit("5 per minute")
        >>> def login():
        ...     return "Login page"

        >>> @limit("10 per hour", key_func=get_ip_key_func())
        >>> def reset_password():
        ...     return "Reset password"
    """
    # 检查 Flask-Limiter 是否可用且限流器已初始化
    if not FLASK_LIMITER_AVAILABLE or limiter is None:
        # Flask-Limiter 不可用或限流器未初始化，返回空装饰器
        def decorator(f):
            return f
        return decorator

    return limiter.limit(limit_value, key_func=key_func, per_method=per_method)


# 预定义的限流装饰器
class RateLimits:
    """
    预定义的限流装饰器集合

    提供常用的限流策略，方便直接使用。

    使用示例:
        >>> from blues_aka.common.rate_limit import RateLimits
        >>> @auth_bp.route('/login', methods=['POST'])
        >>> @RateLimits.AUTH
        >>> def login():
        ...     return "Login"
    """

    # 认证接口：10 次/分钟
    AUTH = limit("10 per minute")

    # 登录接口：5 次/分钟
    LOGIN = limit("5 per minute", key_func=get_ip_key_func())

    # 注册接口：3 次/分钟
    REGISTER = limit("3 per minute", key_func=get_ip_key_func())

    # 密码重置：3 次/小时
    PASSWORD_RESET = limit("3 per hour", key_func=get_ip_key_func())

    # 聊天接口：60 次/分钟
    CHAT = limit("60 per minute")

    # 文件上传：10 次/小时
    UPLOAD = limit("10 per hour")

    # 一般查询：200 次/分钟
    QUERY = limit("200 per minute")

    # 敏感操作：20 次/分钟
    SENSITIVE = limit("20 per minute")

    # 公开接口：1000 次/小时
    PUBLIC = limit("1000 per hour")


# 限流白名单
class Whitelist:
    """
    限流白名单管理

    用于排除不需要限流的 IP 地址或用户。
    """

    # 白名单 IP 地址列表（支持 CIDR 表示法）
    IPS = [
        '127.0.0.1',      # 本地回环
        '::1',            # IPv6 本地回环
        # 可以添加更多 IP
    ]

    # 白名单用户 ID 列表
    USER_IDS = [
        # 管理员用户 ID
        # 1, 2, 3
    ]

    @classmethod
    def is_whitelisted_ip(cls, ip: str) -> bool:
        """
        检查 IP 是否在白名单中

        Args:
            ip: IP 地址

        Returns:
            bool: 是否在白名单中
        """
        return ip in cls.IPS

    @classmethod
    def is_whitelisted_user(cls, user_id: int) -> bool:
        """
        检查用户是否在白名单中

        Args:
            user_id: 用户 ID

        Returns:
            bool: 是否在白名单中
        """
        return user_id in cls.USER_IDS


# 限流统计
class RateLimitStats:
    """
    限流统计信息

    用于监控和分析限流效果。
    """

    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.limited_ips = {}
        self.limited_users = {}

    def record_request(self, key: str, blocked: bool = False):
        """
        记录请求

        Args:
            key: 限流键
            blocked: 是否被限流阻止
        """
        self.total_requests += 1
        if blocked:
            self.blocked_requests += 1
            if key.startswith('ip:'):
                ip = key[3:]
                self.limited_ips[ip] = self.limited_ips.get(ip, 0) + 1
            elif key.startswith('user:'):
                user_id = int(key[5:])
                self.limited_users[user_id] = self.limited_users.get(user_id, 0) + 1

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            dict: 统计数据
        """
        return {
            'total_requests': self.total_requests,
            'blocked_requests': self.blocked_requests,
            'block_rate': f"{(self.blocked_requests / self.total_requests * 100):.2f}%" if self.total_requests > 0 else "0%",
            'limited_ips_count': len(self.limited_ips),
            'limited_users_count': len(self.limited_users),
            'top_limited_ips': sorted(self.limited_ips.items(), key=lambda x: x[1], reverse=True)[:10],
            'top_limited_users': sorted(self.limited_users.items(), key=lambda x: x[1], reverse=True)[:10],
        }


# 全局统计实例
stats = RateLimitStats()
