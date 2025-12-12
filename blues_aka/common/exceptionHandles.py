import time
from http.client import HTTPException

from flask import jsonify

from exception import BaseException

def register_error_handlers(app):
    """注册全局异常处理器"""
    @app.errorhandler(BaseException)
    def handle_business_exception(error):
        # 错误日志
        app.logger.error(
            f"自定义异常：{error.message}",
            extra = {
                'request_id': error.request_id,
                'status_code': error.code,
                'message': error.message,
                'error_code': error.error_code,
            }
        )

        response = jsonify({
            'status': 'error',
            'request_id': error.request_id,
            'code': error.code,
            'message': error.message,
            'data': error.data,
            'timestamp': int(time.time()),
        })

        if error.error_code:
            response.data['status_code'] = error.error_code

        response.status_code = error.code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        # 错误日志
        app.logger.error(
            f"Http异常：{error.name}",
            extra={
                'request_id': error.request_id,
                'status_code': error.code,
            }
        )

        response = jsonify({
            'status': 'error',
            'request_id': error.request_id,
            'code': error.code,
            'message': error.name,
            'data': error.data,
            'timestamp': int(time.time()),
        })

        response.status_code = error.code
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        # 错误日志
        app.logger.error(
            f"服务器异常：{str(error)}",
            extra={'request_id': error.request_id},
            exc_info=True
        )

        response = jsonify({
            'status': 'error',
            'request_id': error.request_id,
            'code': '500',
            'message': '服务器错误',
            'data': error.data,
            'timestamp': int(time.time()),
        })

        response.status_code = 500
        return response