import logging
from sqlite3 import IntegrityError

from flask import Blueprint, request, app
from marshmallow import ValidationError

from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.user.models import User
from blues_aka.user.schemas import *

from blues_aka.extensions import db

# 设置日志
logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__, url_prefix='/user')

# 管理员查询用户
@user_bp.route('/users', methods=['GET'])
@handle_api_response
def get_users():

    try:
        # 参数校验
        query_schemas = userQuerySchema()
        query_params = query_schemas.load(request.args)

        # 构建查询
        query = User.query

        # 构建查询条件
        if query_params.get('id'):
            query = query.filter(User.id == query_params.get('id'))

        if query_params.get('username'):
            query = query.filter(User.username.like(f"%{query_params.get('username')}%"))

        if query_params.get('email'):
            query = query.filter(User.email.like(f"%{query_params.get('email')}%"))

        # 获取排序方式
        sort_by = query_params.get('sort_by')
        order_by = query_params.get('order_by')
        if sort_by:
            sort_field = getattr(User, sort_by)
            if order_by == 'desc':
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())

        # 分页
        pagination = query.paginate(
            page=query_params.get('page', 1),
            per_page=query_params.get('per_page', 10),
            error_out=False
        )

        # 序列化结果
        user_schema = userQueryRespSchema(many=True)
        users = user_schema.dump(pagination.items)

        # 构建响应数据
        response = {
            'users': users,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
                'total': pagination.total,
            }
        }

        return success(data=response)

    except ValidationError as e:
        raise BusinessException(code=400, message="参数校验失败", error_code="INVALID_PARAMS")

    except Exception as e:
        # 其他异常
        raise BusinessException(code=500, message="查询用户失败", error_code="USER_QUERY_FAILED")


# 创建新用户
@user_bp.route('/users', methods=['POST'])
@handle_api_response
def create_user():
    """
        创建新用户接口
        接收JSON格式的用户数据，验证后创建新用户
    """
    try:
        json_data = request.get_json()

        if json_data is None:
            raise BusinessException(code=400, message="请求体不能为空", error_code="EMPTY_REQUEST_BODY")

        # 参数校验
        create_user = userCreateSchema()
        validated_data = create_user.load(json_data)

        existing_user = User.query.filter(
            User.username == validated_data['username'],
            User.email == validated_data['email'],
        ).first()

        if existing_user:
            field = 'username' if existing_user.username == validated_data['username'] else 'email'
            raise BusinessException(code=409, message=f"{field} 已被使用", error_code="DUPLICATE_USER")

        new_user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            password_hash=validated_data['password'],
        )

        db.session.add(new_user)
        db.session.commit()

        response = userCreateRespSchema()
        result = response.dump(new_user)

        return success(data=result, message='用户创建成功！')

    except ValidationError as e:
        logger.warning(f"用户创建参数验证失败: {e.messages}")
        raise BusinessException(code=400, message="参数校验失败", error_code="INVALID_PARAMS")

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"数据库完整性错误: {str(e)}")
        raise BusinessException(code=409, message="用户创建失败，数据冲突", error_code="DATABASE_INTEGRITY_ERROR")

    except BusinessException as e:
        # 已知的业务异常，直接抛出
        raise e

    except Exception as e:
        db.session.rollback()
        logger.error(f"用户创建失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="用户创建失败", error_code="USER_CREATION_FAILED")

# 修改用户
@user_bp.route('/users/<int: id>', methods=['PUT'])
@handle_api_response
def update_user(id):
    try:
        user = User.query.get(id)
        if not user:
            raise BusinessException(code=404, message="用户不存在", error_code="USER_NOT_FOUND")

        json_data = request.get_json()
        if json_data is None:
            raise BusinessException(code=400, message="请求体不能为空", error_code="EMPTY_REQUEST_BODY")

        update_schema = userUpdateSchema()
        validated_user = update_schema.load(json_data)

        if 'username' in validated_user:
            existing_user = User.query.filter(
                User.username == validated_user['username'],
                User.id != id
            ).first()
            if existing_user:
                raise BusinessException(code=409, message="用户名已被使用", error_code="USERNAME_EXISTS")

        if 'email' in validated_user:
            existing_user = User.query.filter(
                User.email == validated_user['email'],
                User.id != id
            ).first()
            if existing_user:
                raise BusinessException(code=409, message="邮箱已被使用", error_code="EMAIL_EXISTS")

        for key, value in validated_user.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.session.commit()

        response = userUpdateRespSchema()
        result = response.dump(user)
        return success(data=result, message='用户信息更新成功！')

    except ValidationError as e:
        logger.warning(f"用户更新参数验证失败: {e.messages}")
        raise BusinessException(code=400, message="参数校验失败", error_code="INVALID_PARAMS")

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"数据库完整性错误: {str(e)}")
        raise BusinessException(code=409, message="用户更新失败，数据冲突", error_code="DATABASE_INTEGRITY_ERROR")

    except BusinessException as e:
        # 已知的业务异常，直接抛出
        raise e

    except Exception as e:
        db.session.rollback()
        logger.error(f"用户更新失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="用户更新失败", error_code="USER_UPDATE_FAILED")

# 删除用户
@user_bp.route('/users/<int:id>', methods=['DELETE'])
@handle_api_response
def delete_user(id):
    """
    删除用户接口
    根据用户ID删除用户
    """
    try:
        user = User.query.get(id)
        if not user:
            raise BusinessException(code=404, message="用户不存在", error_code="USER_NOT_FOUND")

        db.session.delete(user)
        db.session.commit()

        return success(message='用户删除成功！')

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"数据库完整性错误: {str(e)}")
        raise BusinessException(code=409, message="用户删除失败，存在关联数据", error_code="DATABASE_INTEGRITY_ERROR")

    except BusinessException as e:
        # 已知的业务异常，直接抛出
        raise e

    except Exception as e:
        db.session.rollback()
        logger.error(f"用户删除失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="用户删除失败", error_code="USER_DELETE_FAILED")




