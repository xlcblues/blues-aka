import logging

from flask import Blueprint, request
from flask_jwt_extended import create_refresh_token, create_access_token, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.extensions import db
from blues_aka.user.models import User
from blues_aka.user.schemas import userRegisterSchema, userLoginSchema, userRegisterRespSchema

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

        if not user:
            raise BusinessException(400, '找不到用户')
        if not user.check_password(password):
            raise BusinessException(401, '用户名或密码错误')

        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
        }

        db.session.commit()
        logger.info("登录成功！")
        return success(data=data)

    except BusinessException as e:
        raise e

    except Exception as e:
        raise e

@auth_bp.route('/logout', methods=['POST'])
@handle_api_response
def logout():
    try:
        current_username = get_jwt_identity()
        db.session.commit()
        logger.info("登出成功！")
        return success(current_username)

    except BusinessException as e:
        raise e

    except Exception as e:
        raise e

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
            raise BusinessException(400, "用户名已存在")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        result = userRegisterRespSchema().dump(user)

        return success(data=result, message='用户注册成功！')

    except ValidationError as e:
        logger.warning(f"用户创建参数验证失败: {e.messages}")
        raise BusinessException(code=400, message="参数校验失败", error_code="INVALID_PARAMS")

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"数据库完整性错误: {str(e)}")
        raise BusinessException(code=409, message="用户创建失败，数据冲突", error_code="DATABASE_INTEGRITY_ERROR")

    except BusinessException as e:
        raise e

    except Exception as e:
        db.session.rollback()
        logger.error(f"用户创建失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="用户注册失败", error_code="USER_CREATION_FAILED")

