import logging
from flask import Blueprint, request, app
from marshmallow import ValidationError

from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.user.models import User
from blues_aka.user.schemas import userQuerySchema
from blues_aka.user.schemas import userQueryRespSchema

# 设置日志
logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__, url_prefix='/user')

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
        raise BusinessException(
            code=400,
            message="参数校验失败",
            error_code="INVALID_PARAMS"
        )

    except Exception as e:
        # 其他异常
        raise BusinessException(
            code=500,
            message="查询用户失败",
            error_code="USER_QUERY_FAILED",
        )




