import logging

from flask import Blueprint, request

from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.extensions import db
from blues_aka.user.models import User
from blues_aka.user.schemas.authSchemas import userLoginSchema

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
        if not user.checkPassword(password):
            raise BusinessException(401, '用户名或密码错误')

        db.session.commit()
        logger.info("登录成功！")
        return success()
    except BusinessException as e:
        raise e
    except Exception as e:
        raise e

@auth_bp.route('/logout', methods=['POST'])
@handle_api_response
def logout():
    try:
        db.session.commit()
        logger.info("登出成功！")
        return success()
    except BusinessException as e:
        raise e
    except Exception as e:
        raise e

