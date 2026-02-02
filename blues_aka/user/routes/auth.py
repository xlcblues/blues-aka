import datetime
import logging

from flask import Blueprint, request
from flask_jwt_extended import create_refresh_token, create_access_token, get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from blues_aka.common.error_codes import ErrorCodes
from blues_aka.common.exception import BusinessException
from blues_aka.common.exceptions import Exceptions, E
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.extensions import db
from blues_aka.user.models import User
from blues_aka.user.schemas import userRegisterSchema, userLoginSchema, userRegisterRespSchema
from blues_aka.user.utils import get_client_ip, get_ip_location

# 设置日志
logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 登录
@auth_bp.route('/login', methods=['POST'])
@handle_api_response
def login():
    try:
        data = userLoginSchema().load(request.get_json())

        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()
        logger.info("校验中")

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
def logout():
    """
    用户登出接口

    注意：JWT 是无状态的，实际的登出需要在前端删除 token。
    如果需要强制失效 token，应该实现 token 黑名单机制。

    Returns:
        Response: 包含用户 ID 的成功响应
    """
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"用户 {current_user_id} 登出成功")

        # TODO: 实现 token 黑名单机制以强制失效 token
        # 可以将 token 添加到 Redis 黑名单中，设置过期时间

        return success({'user_id': current_user_id, 'message': '登出成功'})

    except BusinessException as e:
        raise e
    except Exception as e:
        logger.error(f"登出失败: {str(e)}", exc_info=True)
        raise E.Common.internal_server_error()

@auth_bp.route('/register', methods=['POST'])
@handle_api_response
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
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or user.is_deleted:
            raise E.User.user_not_found()

        # 创建新的 access token
        access_token = create_access_token(identity=user.id)

        return success(data={'access_token': access_token})

    except BusinessException as e:
        raise e

    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="刷新令牌失败", error_code=ErrorCodes.User.REFRESH_TOKEN_FAILED)


