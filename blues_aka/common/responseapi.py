from functools import wraps
from flask import jsonify

from blues_aka.common.response import create_response, success
from blues_aka.common.exception import BusinessException


def handle_api_response(f):
    """
    API响应处理装饰器，自动处理返回值和异常

    用法：
    @app.route('/api/example')
    @handle_api_response
    def example():
        # 可以直接返回数据，会自动包装为统一格式
        return {"key": "value"}

        # 或者抛出业务异常，会被自动捕获并转换为统一错误格式
        raise BusinessException("Something went wrong", 400)
    """
    @wraps(f)
    def wrapper(*args, **kwargs):

        try:
            result = f(*args, **kwargs)

            # 如果返回的是元组 (response, status)
            if isinstance(result, tuple) and len(result) == 2:
                data, status = result
                return create_response(data=data, status=status)

            # 如果已经是Flask响应对象，直接返回
            if hasattr(result, 'status_code'):
                return result

            # 否则包装为成功响应
            return success(data=result)

        except BusinessException as e:
            # 捕获业务异常并转换为JSON响应
            response = jsonify({
                'code': e.code,
                'message': e.message,
                'error_code': e.error_code
            })
            response.status_code = e.code
            return response

        except Exception as e:
            # 捕获其他未处理的异常
            response = jsonify({
                'code': 500,
                'message': str(e),
                'error_code': 'INTERNAL_SERVER_ERROR'
            })
            response.status_code = 500
            return response

    return wrapper

