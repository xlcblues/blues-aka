import time
import uuid

from werkzeug.exceptions import HTTPException  # ✅ 修改这里

from flask import jsonify
from blues_aka.common.exception import BusinessException  # ✅ 修改导入路径


def register_error_handlers(app):
    """注册全局异常处理器"""

    @app.errorhandler(BusinessException)
    def handle_business_exception(error):
        """处理业务异常"""
        # 错误日志
        app.logger.error(
            f"业务异常: {error.message}",
            extra={
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

        response.status_code = error.code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """处理 HTTP 异常"""
        # 为 HTTPException 添加 request_id
        request_id = str(uuid.uuid4())

        # 错误日志
        app.logger.error(
            f"HTTP异常: {error.name}",
            extra={
                'request_id': request_id,
                'status_code': error.code,
                'description': error.description,
            }
        )

        response = jsonify({
            'status': 'error',
            'request_id': request_id,
            'code': error.code,
            'message': error.name,
            'data': {'description': error.description} if error.description else {},
            'timestamp': int(time.time()),
        })

        response.status_code = error.code
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """处理通用异常"""
        # 生成 request_id
        request_id = str(uuid.uuid4())

        # 错误日志 - 不要在生产环境暴露详细错误信息
        app.logger.error(
            f"服务器异常: {str(error)}",
            extra={
                'request_id': request_id,
                'type': type(error).__name__,
            },
            exc_info=True
        )

        # 生产环境不要返回详细的错误信息
        response = jsonify({
            'status': 'error',
            'request_id': request_id,
            'code': 500,
            'message': '服务器内部错误',
            'data': {},
            'timestamp': int(time.time()),
        })

        response.status_code = 500
        return response

    # 注册 404 处理器
    @app.errorhandler(404)
    def handle_not_found(error):
        """处理 404 错误"""
        request_id = str(uuid.uuid4())

        response = jsonify({
            'status': 'error',
            'request_id': request_id,
            'code': 404,
            'message': '请求的资源不存在',
            'data': {},
            'timestamp': int(time.time()),
        })

        response.status_code = 404
        return response