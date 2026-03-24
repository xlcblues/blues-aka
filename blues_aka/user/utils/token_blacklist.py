"""
JWT Token 黑名单管理模块

本模块提供 JWT token 黑名单功能，用于实现用户登出时强制失效 token。
通过使用缓存系统（Redis或内存缓存）来存储被吊销的 token。

主要功能:
    - 将 token 添加到黑名单
    - 检查 token 是否在黑名单中
    - 自动清理过期的黑名单记录
    - 支持批量吊销用户的所有 token

设计原则:
    - 使用缓存实现，性能高
    - token 过期时间与缓存过期时间同步
    - 支持 access_token 和 refresh_token
    - 失败不影响主流程

使用场景:
    1. 用户主动登出时，将当前 token 加入黑名单
    2. 管理员强制用户下线
    3. 安全原因需要立即失效 token
    4. 密码修改后失效所有旧 token
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from flask import request
from flask_jwt_extended import decode_token, get_jwt

from blues_aka.common.cache import get_cache


# 配置日志记录器
logger = logging.getLogger(__name__)


class TokenBlacklist:
    """
    Token 黑名单管理器

    提供完整的 token 黑名单功能，包括添加、检查、删除等操作。
    使用缓存系统（Redis 或内存缓存）存储黑名单数据。
    """

    # 黑名单键前缀
    BLACKLIST_PREFIX = 'token_blacklist'

    # 用户所有 token 黑名单前缀
    USER_TOKENS_PREFIX = 'user_tokens'

    def __init__(self):
        """初始化 Token 黑名单管理器"""
        self.cache = get_cache()
        # 如果缓存不可用，使用内存缓存作为后备
        if self.cache is None:
            from blues_aka.common.cache import MemoryCacheBackend, CacheManager
            logger.warning("缓存系统未初始化，使用内存缓存作为 token 黑名单后端")
            self.cache = CacheManager(MemoryCacheBackend(), prefix='token_blacklist_fallback')

    def _get_token_jti(self, token: Optional[str] = None) -> Optional[str]:
        """
        获取 token 的 JTI (JWT ID)

        Args:
            token: JWT token 字符串，如果为 None 则从当前请求上下文中获取

        Returns:
            str: token 的 JTI，如果解析失败则返回 None

        Note:
            JTI 是 JWT 的唯一标识符，用于区分不同的 token
        """
        try:
            if token:
                # 解码提供的 token
                decoded = decode_token(token)
            else:
                # 从当前 JWT 上下文获取
                decoded = get_jwt()

            # 返回 JTI
            return decoded.get('jti')

        except Exception as e:
            logger.error(f"获取 token JTI 失败: {str(e)}", exc_info=True)
            return None

    def _get_token_exp(self, token: Optional[str] = None) -> Optional[datetime]:
        """
        获取 token 的过期时间

        Args:
            token: JWT token 字符串，如果为 None 则从当前请求上下文中获取

        Returns:
            datetime: token 的过期时间，如果解析失败则返回 None
        """
        try:
            if token:
                decoded = decode_token(token)
            else:
                decoded = get_jwt()

            exp = decoded.get('exp')
            if exp:
                # 将时间戳转换为 datetime
                return datetime.fromtimestamp(exp)

            return None

        except Exception as e:
            logger.error(f"获取 token 过期时间失败: {str(e)}", exc_info=True)
            return None

    def _get_blacklist_key(self, jti: str) -> str:
        """
        生成黑名单缓存键

        Args:
            jti: token 的 JTI

        Returns:
            str: 黑名单缓存键
        """
        return f"{self.BLACKLIST_PREFIX}:{jti}"

    def _get_user_tokens_key(self, user_id: int) -> str:
        """
        生成用户所有 token 的缓存键

        Args:
            user_id: 用户 ID

        Returns:
            str: 用户 token 缓存键
        """
        return f"{self.USER_TOKENS_PREFIX}:{user_id}"

    def add(self, token: Optional[str] = None, reason: str = "logout") -> bool:
        """
        将 token 添加到黑名单

        Args:
            token: JWT token 字符串，如果为 None 则从当前请求上下文获取
            reason: 加入黑名单的原因（用于日志记录）

        Returns:
            bool: 是否成功添加到黑名单

        Note:
            - 缓存过期时间设置为 token 的剩余有效时间
            - token 过期后自动从黑名单移除
            - 失败不影响主流程，只记录日志

        Example:
            >>> blacklist = TokenBlacklist()
            >>> success = blacklist.add(reason="用户主动登出")
            >>> if success:
            ...     print("Token 已加入黑名单")
        """
        try:
            # 获取 token 的 JTI 和过期时间
            jti = self._get_token_jti(token)
            if not jti:
                logger.warning("无法获取 token JTI，无法添加到黑名单")
                return False

            exp = self._get_token_exp(token)
            if not exp:
                logger.warning("无法获取 token 过期时间，使用默认值")
                # 默认缓存 24 小时
                timeout = 86400
            else:
                # 计算剩余有效时间（秒）
                now = datetime.now()
                if exp > now:
                    timeout = int((exp - now).total_seconds())
                else:
                    # token 已过期，不需要添加到黑名单
                    logger.info(f"Token 已过期，无需添加到黑名单: jti={jti}")
                    return False

            # 添加到黑名单
            blacklist_key = self._get_blacklist_key(jti)
            blacklist_data = {
                'jti': jti,
                'reason': reason,
                'added_at': datetime.now().isoformat(),
                'expires_at': exp.isoformat() if exp else None
            }

            success = self.cache.set(blacklist_key, blacklist_data, timeout=timeout)

            if success:
                logger.info(
                    f"Token 已加入黑名单: jti={jti}, "
                    f"reason={reason}, timeout={timeout}秒"
                )
            else:
                logger.warning(f"Token 加入黑名单失败: jti={jti}")

            return success

        except Exception as e:
            logger.error(f"添加 token 到黑名单时发生错误: {str(e)}", exc_info=True)
            return False

    def check(self, token: Optional[str] = None) -> bool:
        """
        检查 token 是否在黑名单中

        Args:
            token: JWT token 字符串，如果为 None 则从当前请求上下文获取

        Returns:
            bool: token 是否在黑名单中

        Example:
            >>> blacklist = TokenBlacklist()
            >>> if blacklist.check():
            ...     print("Token 已被吊销")
        """
        try:
            jti = self._get_token_jti(token)
            if not jti:
                return False

            blacklist_key = self._get_blacklist_key(jti)
            exists = self.cache.exists(blacklist_key)

            if exists:
                logger.info(f"Token 在黑名单中: jti={jti}")

            return exists

        except Exception as e:
            logger.error(f"检查 token 黑名单时发生错误: {str(e)}", exc_info=True)
            # 出错时返回 False，避免影响正常请求
            return False

    def remove(self, token: Optional[str] = None) -> bool:
        """
        从黑名单中移除 token（解除吊销）

        Args:
            token: JWT token 字符串，如果为 None 则从当前请求上下文获取

        Returns:
            bool: 是否成功移除

        Note:
            此功能用于特殊情况，通常不需要手动移除
            token 会随着缓存过期自动移除

        Example:
            >>> blacklist = TokenBlacklist()
            >>> success = blacklist.remove()
        """
        try:
            jti = self._get_token_jti(token)
            if not jti:
                return False

            blacklist_key = self._get_blacklist_key(jti)
            success = self.cache.delete(blacklist_key)

            if success:
                logger.info(f"Token 已从黑名单移除: jti={jti}")

            return success

        except Exception as e:
            logger.error(f"从黑名单移除 token 时发生错误: {str(e)}", exc_info=True)
            return False

    def revoke_user_tokens(self, user_id: int, reason: str = "admin_revoke") -> int:
        """
        吊销用户的所有 token

        Args:
            user_id: 用户 ID
            reason: 吊销原因

        Returns:
            int: 被吊销的 token 数量

        Note:
            此功能用于强制用户下线，例如：
            - 管理员封禁用户
            - 用户修改密码后失效所有旧 token
            - 安全原因需要立即失效所有会话

        Example:
            >>> blacklist = TokenBlacklist()
            >>> count = blacklist.revoke_user_tokens(user_id=123, reason="密码已修改")
            >>> print(f"已吊销 {count} 个 token")
        """
        try:
            # 获取用户的所有 token JTI 列表
            user_tokens_key = self._get_user_tokens_key(user_id)
            user_tokens = self.cache.get(user_tokens_key)

            if not user_tokens:
                logger.info(f"用户 {user_id} 没有活跃的 token")
                return 0

            # 将所有 token 添加到黑名单
            revoked_count = 0
            for token_info in user_tokens:
                jti = token_info.get('jti')
                if jti:
                    # 获取 token 的剩余有效时间
                    added_at = datetime.fromisoformat(token_info.get('added_at'))
                    expires_at = datetime.fromisoformat(token_info.get('expires_at'))

                    now = datetime.now()
                    if expires_at > now:
                        timeout = int((expires_at - now).total_seconds())

                        # 添加到黑名单
                        blacklist_key = self._get_blacklist_key(jti)
                        blacklist_data = {
                            'jti': jti,
                            'reason': reason,
                            'added_at': now.isoformat(),
                            'expires_at': expires_at.isoformat()
                        }

                        if self.cache.set(blacklist_key, blacklist_data, timeout=timeout):
                            revoked_count += 1

            # 清除用户的 token 列表
            self.cache.delete(user_tokens_key)

            logger.info(
                f"已吊销用户 {user_id} 的所有 token: "
                f"count={revoked_count}, reason={reason}"
            )

            return revoked_count

        except Exception as e:
            logger.error(f"吊销用户 token 时发生错误: {str(e)}", exc_info=True)
            return 0

    def cleanup_expired(self) -> int:
        """
        清理已过期的黑名单记录

        Returns:
            int: 清理的记录数量

        Note:
            通常不需要手动调用，因为缓存会自动过期
            此方法用于维护或调试目的
        """
        try:
            # 注意：Redis 和内存缓存都会自动过期
            # 这里只是记录日志，实际清理由缓存系统自动处理
            logger.info("黑名单记录会由缓存系统自动过期清理")
            return 0

        except Exception as e:
            logger.error(f"清理过期黑名单时发生错误: {str(e)}", exc_info=True)
            return 0


# 创建全局黑名单实例
token_blacklist = TokenBlacklist()


def init_token_blacklist(app):
    """
    初始化 token 黑名单系统

    Args:
        app: Flask 应用实例
    """
    # 确保缓存系统已初始化
    cache = get_cache()
    if not cache:
        logger.warning("缓存系统未初始化，token 黑名单功能可能不可用")
    else:
        logger.info("Token 黑名单系统初始化完成")


def check_if_token_revoked(jwt_header: dict, jwt_payload: dict) -> bool:
    """
    JWT 回调函数：检查 token 是否被吊销

    这个函数会在每次验证 JWT token 时被 Flask-JWT-Extended 调用。
    如果返回 True，则认为 token 已被吊销，拒绝访问。

    Args:
        jwt_header: JWT 头部信息
        jwt_payload: JWT 载荷数据

    Returns:
        bool: token 是否被吊销

    Example:
        在 Flask-JWT-Extended 配置中使用:
        app.config['JWT_TOKEN_IN_BLOCKLIST_TOKEN_LOADER'] = check_if_token_revoked
    """
    try:
        # 从载荷中获取 JTI
        jti = jwt_payload.get('jti')
        if not jti:
            return False

        # 检查是否在黑名单中
        blacklist = TokenBlacklist()
        return blacklist.check_by_jti(jti)

    except Exception as e:
        logger.error(f"检查 token 吊销状态时发生错误: {str(e)}", exc_info=True)
        # 出错时返回 False，避免影响正常请求
        return False


# 扩展 TokenBlacklist 类，添加 check_by_jti 方法
def _check_by_jti(self, jti: str) -> bool:
    """
    通过 JTI 检查 token 是否在黑名单中

    Args:
        jti: token 的 JTI

    Returns:
        bool: token 是否在黑名单中
    """
    try:
        blacklist_key = self._get_blacklist_key(jti)
        return self.cache.exists(blacklist_key)
    except Exception as e:
        logger.error(f"检查 token 黑名单时发生错误: {str(e)}", exc_info=True)
        return False


# 动态添加方法到类
TokenBlacklist.check_by_jti = _check_by_jti
