import logging
from sqlite3 import IntegrityError

from flask import Blueprint, request, app
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from marshmallow import ValidationError

from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.common.utils import SortValidator, require_admin
from blues_aka.user.models import User

from blues_aka.extensions import db
from blues_aka.user.schemas import userCreateSchema, userUpdateSchema, userUpdateRespSchema, userQuerySchema, userQueryRespSchema, userCreateRespSchema

# 设置日志
logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__, url_prefix='/user')

# 管理员查询用户
@user_bp.route('/users', methods=['GET'])
@handle_api_response
@require_admin
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

        if query_params.get('nickname'):
            query = query.filter(User.nickname.like(f"%{query_params.get('nickname')}%"))

        if query_params.get('phone'):
            query = query.filter(User.phone.like(f"%{query_params.get('phone')}%"))

        # 定义允许排序的字段
        ALLOWED_SORT_FIELDS = {
            'id', 'username', 'email', 'nickname',
            'phone', 'role', 'status', 'created_at', 'updated_at'
        }

        # 使用通用排序工具
        sort_by = query_params.get('sort_by')
        order_by = query_params.get('order_by')

        query = SortValidator.validate_and_apply_sort(
            query=query,
            model=User,
            sort_by=sort_by,
            order_by=order_by,
            allowed_fields=ALLOWED_SORT_FIELDS,
            default_field='created_at',
            default_order='desc'
        )

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
@require_admin
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

        # 检查用户名是否已存在
        existing_user = User.query.filter(
            User.username == validated_data['username']
        ).first()

        if existing_user:
            raise BusinessException(code=409, message="用户名已被使用", error_code="DUPLICATE_USERNAME")

        # 检查邮箱是否已存在
        existing_user = User.query.filter(
            User.email == validated_data['email']
        ).first()

        if existing_user:
            raise BusinessException(code=409, message="邮箱已被使用", error_code="DUPLICATE_EMAIL")

        # 创建用户对象，处理可选字段
        new_user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            password_hash=validated_data['password'],
        )

        # 添加可选字段
        if 'nickname' in validated_data and validated_data['nickname']:
            new_user.nickname = validated_data['nickname']

        if 'phone' in validated_data and validated_data['phone']:
            new_user.phone = validated_data['phone']

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
@user_bp.route('/users/<int:id>', methods=['PUT'])
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
            # 特殊处理密码字段
            if key == 'password':
                if value:  # 如果提供了新密码
                    try:
                        user.set_password(value)
                    except ValueError as e:
                        logger.warning(f"密码强度不足: {str(e)}")
                        raise BusinessException(400, str(e), "WEAK_PASSWORD")
            elif hasattr(user, key):
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
@require_admin
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

@user_bp.route('/users/<int:id>/change-password', methods=['POST'])
@jwt_required()
@handle_api_response
def change_password(id):
    """修改用户密码"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"用户 {user_id} 尝试修改用户 {id} 的密码")

        if id != user_id and not current_user.is_admin:
            logger.warning(f"用户 {user_id} 无权修改用户 {id} 的密码")
            raise BusinessException(403, "无权限", "FORBIDDEN")

        user = User.query.get(id)
        if not user:
            logger.warning(f"用户 {id} 不存在")
            raise BusinessException(404, "用户不存在", "USER_NOT_FOUND")

        json_data = request.get_json()
        current_password = json_data.get('password')
        new_password = json_data.get('new_password')

        if not current_password or not new_password:
            logger.warning("密码参数不完整")
            raise BusinessException(400, "密码参数不完整", "INVALID_PARAMS")

        logger.info(f"验证用户 {user.username} 的当前密码")
        if not user.check_password(current_password):
            logger.warning(f"用户 {user.username} 的当前密码验证失败")
            raise BusinessException(400, "当前密码不正确", "INVALID_CURRENT_PASSWORD")

        try:
            logger.info(f"为用户 {user.username} 设置新密码")
            user.set_password(new_password)
            db.session.commit()
            logger.info(f"用户 {user.username} 密码修改成功")
            return success(message="密码修改成功")

        except ValueError as e:
            logger.warning(f"新密码强度不足: {str(e)}")
            raise BusinessException(400, str(e), "WEAK_PASSWORD")

    except BusinessException as e:
        raise e
    except Exception as e:
        logger.error(f"密码修改失败: {str(e)}", exc_info=True)
        raise BusinessException(500, "密码修改失败", "PASSWORD_CHANGE_FAILED")


