import datetime
import logging

from flask import Blueprint, request
from flask_jwt_extended import create_refresh_token, create_access_token, get_jwt_identity, jwt_required, get_jwt
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from blues_aka.common.error_codes import ErrorCodes
from blues_aka.common.exception import BusinessException
from blues_aka.common.exceptions import Exceptions, E
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.common.rate_limit import RateLimits
from blues_aka.extensions import db
from blues_aka.user.models import User
from blues_aka.user.schemas import userRegisterSchema, userLoginSchema, userRegisterRespSchema
from blues_aka.user.utils import get_client_ip, get_ip_location
from blues_aka.user.utils.token_blacklist import token_blacklist

# 设置日志
logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 登录
@auth_bp.route('/login', methods=['POST'])
@handle_api_response
@RateLimits.LOGIN  # 5 次/分钟，基于 IP 限流
def login():
    try:
        data = userLoginSchema().load(request.get_json())

        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()
        logger.debug("校验中")

        if not user or user.is_deleted:
            raise E.User.user_not_found()
        if not user.check_password(password):
            raise E.User.invalid_credentials()

        # 使用 user.id 作为 JWT identity
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
        }

        user.login_count += 1
        user.last_login_at = datetime.datetime.now()
        user.last_login_ip = get_client_ip()
        user.status = 'active'
        db.session.commit()
        return success(data=data)

    except BusinessException as e:
        raise E.User.invalid_credentials()

    except Exception as e:
        raise e

@auth_bp.route('/logout', methods=['POST'])
@handle_api_response
@jwt_required()
def logout():
    """
    用户登出接口

    将当前 token 添加到黑名单，强制失效该 token。
    前端需要删除本地存储的 token。

    请求方法: POST
    认证要求: 需要 JWT Token

    Returns:
        Response: 包含用户 ID 和成功消息的响应

    业务逻辑:
        1. 获取当前用户 ID 和 token 信息
        2. 将当前 token 添加到黑名单
        3. 记录登出日志

    异常处理:
        - 黑名单添加失败不影响登出流程
        - 即使 token 黑名单失败，也返回成功（因为前端应删除本地 token）

    注意事项:
        - JWT access token 和 refresh token 都会被吊销
        - token 在黑名单中的有效期与原 token 的剩余有效时间相同
        - 前端应该删除本地存储的所有 token
        - 使用 token 黑名单机制，确保被吊销的 token 无法继续使用

    Example:
        POST /auth/logout
        Headers: Authorization: Bearer <access_token>

        Response:
        {
            "code": 200,
            "message": "登出成功",
            "data": {
                "user_id": 123,
                "message": "Token 已被吊销"
            }
        }
    """
    try:
        current_user_id = get_jwt_identity()
        current_token_jti = get_jwt().get('jti')

        logger.info(f"用户 {current_user_id} (token_jti: {current_token_jti}) 请求登出")

        # 将当前 access token 添加到黑名单
        success_add = token_blacklist.add(reason="用户主动登出")

        if success_add:
            logger.info(f"用户 {current_user_id} 登出成功，token 已加入黑名单")
            message = "登出成功，Token 已被吊销"
        else:
            logger.warning(f"用户 {current_user_id} 登出成功，但 token 黑名单添加失败")
            message = "登出成功（Token 吊销失败，但前端应删除本地 token）"

        return success({
            'user_id': current_user_id,
            'message': message,
            'token_revoked': success_add
        })

    except BusinessException as e:
        raise e
    except Exception as e:
        logger.error(f"登出失败: {str(e)}", exc_info=True)
        raise E.Common.internal_server_error()

@auth_bp.route('/register', methods=['POST'])
@handle_api_response
@RateLimits.REGISTER  # 3 次/分钟，基于 IP 限流
def register():
    try:
        data = userRegisterSchema().load(request.get_json())

        username = data['username']
        password = data['password']
        email = data['email']

        user = User.query.filter_by(username=username).first()
        if user:
            raise E.User.duplicate_username()

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        result = userRegisterRespSchema().dump(user)

        return success(data=result, message='用户注册成功！')

    except ValidationError as e:
        logger.warning(f"用户创建参数验证失败: {e.messages}")
        raise E.Common.invalid_params()

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"数据库完整性错误: {str(e)}")
        raise E.Common.database_error()

    except BusinessException as e:
        raise e

    except Exception as e:
        db.session.rollback()
        logger.error(f"用户创建失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="用户注册失败", error_code="USER_CREATION_FAILED")

@auth_bp.route('/me', methods=['GET'])
@handle_api_response
@jwt_required()
def get_current_user():
    """
    获取当前登录用户信息
    """
    try:

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or user.is_deleted:
            raise E.User.user_not_found()

        # 返回用户基本信息，包含is_admin字段
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'nickname': user.nickname,
            'phone': user.phone,
            'is_admin': user.is_admin,
            'status': user.status,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None
        }

        return success(data=user_data)

    except BusinessException as e:
        raise e

    except Exception as e:
        logger.error(f"获取当前用户信息失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="获取用户信息失败", error_code=ErrorCodes.User.USER_QUERY_FAILED)


@auth_bp.route('/refresh', methods=['POST'])
@handle_api_response
@jwt_required(refresh=True)
def refresh():
    """
    刷新访问令牌

    使用 refresh token 获取新的 access token。
    如果 refresh token 在黑名单中，则拒绝刷新。

    请求方法: POST
    认证要求: 需要 JWT Refresh Token

    Returns:
        Response: 包含新 access token 的响应

    业务逻辑:
        1. 验证 refresh token 是否有效
        2. 检查 refresh token 是否在黑名单中
        3. 验证用户是否存在且有效
        4. 创建新的 access token
        5. 返回新的 access token

    异常处理:
        - 用户不存在: 返回用户未找到错误
        - 用户已删除: 返回用户未找到错误
        - refresh token 被吊销: 返回 token 无效错误

    安全措施:
        - 检查 refresh token 是否在黑名单中
        - 验证用户状态
        - 记录刷新操作日志

    注意事项:
        - refresh token 本身不会被吊销（除非用户主动登出或管理员操作）
        - 新的 access token 有效期由系统配置决定
        - 建议前端在 access token 过期前自动刷新

    Example:
        POST /auth/refresh
        Headers: Authorization: Bearer <refresh_token>

        Response:
        {
            "code": 200,
            "message": "成功",
            "data": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            }
        }
    """
    try:
        current_user_id = get_jwt_identity()
        refresh_jti = get_jwt().get('jti')

        logger.info(f"用户 {current_user_id} (refresh_jti: {refresh_jti}) 请求刷新 token")

        # 检查 refresh token 是否在黑名单中
        if token_blacklist.check():
            logger.warning(
                f"拒绝刷新: refresh token 在黑名单中 - "
                f"user_id={current_user_id}, jti={refresh_jti}"
            )
            raise E.Auth.invalid_token("Refresh token 已被吊销，请重新登录")

        # 验证用户
        user = User.query.get(current_user_id)

        if not user or user.is_deleted:
            raise E.User.user_not_found()

        # 检查用户状态
        if user.status == 'suspended':
            raise E.Auth.account_suspended("账户已暂停，无法刷新 token")
        elif user.status == 'deleted':
            raise E.User.user_not_found()

        # 创建新的 access token
        access_token = create_access_token(identity=user.id)

        logger.info(f"用户 {current_user_id} token 刷新成功")

        return success(data={
            'access_token': access_token,
            'token_type': 'Bearer'
        })

    except BusinessException as e:
        raise e

    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}", exc_info=True)
        raise E.Auth.invalid_token("刷新令牌失败，请重新登录")


