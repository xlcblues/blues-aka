from functools import wraps

from blues_aka.common.response import create_response, success


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
                create_response(data=data, status=status)

            # 如果已经是Flask响应对象，直接返回
            if hasattr(result, 'status_code'):
                return result

            # 否则包装为成功响应
            return success(data=result)

        except BaseException as e:
            raise e

        except Exception as e:
            raise e

    return wrapper

