# blues_aka/common/utils.py
from functools import wraps
from typing import Type, Set, Any

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from sqlalchemy.orm import Query
from sqlalchemy import Column
from sqlalchemy.sql.functions import current_user

from blues_aka.common.exception import BusinessException
from blues_aka.user.models import User


class SortValidator:
    """排序参数验证器"""

    @staticmethod
    def validate_and_apply_sort(
        query: Query,
        model: Type,
        sort_by: str,
        order_by: str,
        allowed_fields: Set[str],
        default_field: str = 'created_at',
        default_order: str = 'desc'
    ) -> Query:

        # 规范化输入
        order_by = (order_by or default_order).lower()
        sort_by = sort_by or default_field

        # 验证排序方向
        if order_by not in {'asc', 'desc'}:
            raise BusinessException(
                code=400,
                message=f"排序方向只能是 'asc' 或 'desc'，当前值: {order_by}",
                error_code="INVALID_ORDER_DIRECTION"
            )

        # 验证排序字段
        if sort_by not in allowed_fields:
            raise BusinessException(
                code=400,
                message=f"不支持的排序字段: {sort_by}",
                error_code="INVALID_SORT_FIELD"
            )

        # 安全地获取字段并应用排序
        try:
            sort_field = getattr(model, sort_by)
            if order_by == 'desc':
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())
        except AttributeError as e:
            raise BusinessException(
                code=500,
                message=f"排序字段配置错误: {str(e)}",
                error_code="SORT_CONFIG_ERROR"
            )

        return query

def require_admin(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user is None:
            raise BusinessException(
                code=404,
                message="用户不存在",
                error_code="USER_NOT_FOUND"
            )

        if not user.is_admin:
            raise BusinessException(
                code=403,
                message="权限不足，需要管理员权限",
                error_code="ADMIN_REQUIRED"
            )

        return f(*args, **kwargs)
    return decorated_function
