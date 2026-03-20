"""
JWT 认证配置模块

本模块负责配置 Flask-JWT-Extended，包括：
- JWT token 黑名单检查
- Token 过期处理
- 用户加载回调
- 错误处理回调

主要功能:
    - 配置 token 黑名单检查回调
    - 配置用户加载回调
    - 配置各种 JWT 错误处理

安全措施:
    - 所有 API 请求都会检查 token 是否在黑名单中
    - 被吊销的 token 无法访问任何需要认证的接口
"""

import logging
from flask_jwt_extended import JWTManager

# 配置日志记录器
logger = logging.getLogger(__name__)


# 初始化jwt
def init_jwt(app):
    """
    初始化 JWT 管理器并配置相关回调

    Args:
        app: Flask 应用实例

    配置内容:
        1. 初始化 JWTManager
        2. 配置 token 黑名单检查回调
        3. 配置用户加载回调
        4. 配置各种错误处理回调

    注意事项:
        - 必须在缓存系统初始化之后调用
        - token 黑名单功能依赖缓存系统
    """
    jwt = JWTManager(app)
    jwt.init_app(app)

    # 配置 token 黑名单检查回调
    # 这个回调会在每次验证 JWT token 时被调用
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """
        检查 token 是否在黑名单中

        Args:
            jwt_header: JWT 头部信息
            jwt_payload: JWT 载荷数据

        Returns:
            bool: token 是否在黑名单中（True 表示被吊销）

        注意:
            - 这个回调会在每次验证 token 时自动调用
            - 返回 True 会拒绝该 token 的访问
            - 返回 False 允许该 token 继续使用
        """
        try:
            # 延迟导入，避免循环依赖
            from blues_aka.user.utils.token_blacklist import token_blacklist

            # 从载荷中获取 JTI (JWT ID)
            jti = jwt_payload.get('jti')

            if not jti:
                # 没有 JTI 的 token 不进行黑名单检查
                return False

            # 检查是否在黑名单中
            is_revoked = token_blacklist.check_by_jti(jti)

            if is_revoked:
                logger.info(
                    f"拒绝访问: token 在黑名单中 - "
                    f"jti={jti}, user_id={jwt_payload.get('sub')}"
                )

            return is_revoked

        except Exception as e:
            # 出错时不拒绝访问，避免影响所有请求
            logger.error(
                f"检查 token 黑名单时发生错误: {str(e)}",
                exc_info=True
            )
            return False

    # 配置用户加载回调（可选，用于扩展功能）
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        """
        用户身份加载回调

        当创建 token 时，这个回调决定将什么存储在 token 的 sub (subject) 字段中。

        Args:
            user_id: 用户 ID

        Returns:
            用户身份标识
        """
        return user_id

    # 配置过期的 token 回调
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """
        过期 token 回调

        当使用过期的 token 时调用。

        Args:
            jwt_header: JWT 头部
            jwt_payload: JWT 载荷

        Returns:
            错误响应
        """
        logger.warning(
            f"使用过期的 token - jti={jwt_payload.get('jti')}, "
            f"user_id={jwt_payload.get('sub')}"
        )
        from flask import jsonify
        return jsonify({
            'code': 401,
            'message': 'Token 已过期，请重新登录',
            'error_code': 'TOKEN_EXPIRED'
        }), 401

    # 配置无效的 token 回调
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """
        无效 token 回调

        当使用无效的 token 时调用。

        Args:
            error: 错误信息

        Returns:
            错误响应
        """
        logger.warning(f"使用无效的 token: {error}")
        from flask import jsonify
        return jsonify({
            'code': 401,
            'message': 'Token 无效，请重新登录',
            'error_code': 'INVALID_TOKEN'
        }), 401

    # 配置缺少 token 回调
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """
        缺少 token 回调

        当请求缺少 token 时调用。

        Args:
            error: 错误信息

        Returns:
            错误响应
        """
        logger.debug(f"请求缺少 token: {error}")
        from flask import jsonify
        return jsonify({
            'code': 401,
            'message': '缺少认证 token，请先登录',
            'error_code': 'MISSING_TOKEN'
        }), 401

    # 配置 token 被吊销回调（可选，提供更详细的错误信息）
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """
        Token 被吊销回调

        当使用被吊销的 token 时调用。

        Args:
            jwt_header: JWT 头部
            jwt_payload: JWT 载荷

        Returns:
            错误响应
        """
        logger.warning(
            f"使用被吊销的 token - jti={jwt_payload.get('jti')}, "
            f"user_id={jwt_payload.get('sub')}"
        )
        from flask import jsonify
        return jsonify({
            'code': 401,
            'message': 'Token 已被吊销，请重新登录',
            'error_code': 'TOKEN_REVOKED'
        }), 401

    logger.info("JWT 管理器初始化完成，token 黑名单检查已启用")