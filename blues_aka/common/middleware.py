"""
请求日志中间件
用于记录所有HTTP请求和响应信息，便于问题追踪和审计
"""
import time
import uuid
from flask import request, g
from logging import getLogger

logger = getLogger(__name__)


class RequestLoggingMiddleware:
    """请求日志中间件"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """初始化中间件"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)

    def before_request(self):
        """请求处理前"""
        # 生成唯一请求ID
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()

        # 记录请求信息
        self._log_request()

    def after_request(self, response):
        """请求处理后"""
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
        else:
            duration = 0

        # 记录响应信息
        self._log_response(response, duration)

        # 添加请求ID到响应头
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id

        return response

    def teardown_request(self, exception):
        """请求结束后清理"""
        if exception:
            logger.error(
                f"Request failed: {request.method} {request.path}",
                extra={
                    'request_id': getattr(g, 'request_id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'exception': str(exception)
                }
            )

    def _log_request(self):
        """记录请求信息"""
        # 获取客户端信息
        client_ip = self._get_client_ip()
        user_agent = request.headers.get('User-Agent', '')

        # 获取用户信息（如果已认证）
        user_info = self._get_user_info()

        # 构建日志消息
        log_data = {
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'query_string': request.query_string.decode('utf-8'),
            'client_ip': client_ip,
            'user_agent': user_agent,
            'user_id': user_info.get('user_id'),
            'username': user_info.get('username'),
        }

        # 对于POST/PUT/PATCH请求，记录请求体（但不包括敏感信息）
        if request.method in ['POST', 'PUT', 'PATCH']:
            log_data['body'] = self._sanitize_body(request.get_json(silent=True) or {})

        logger.info(
            f"Incoming request: {request.method} {request.path}",
            extra=log_data
        )

    def _log_response(self, response, duration):
        """记录响应信息"""
        log_data = {
            'request_id': getattr(g, 'request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'response_size': response.content_length or 0,
        }

        # 根据状态码选择日志级别
        if response.status_code >= 500:
            logger.error(
                f"Request failed: {request.method} {request.path} - {response.status_code}",
                extra=log_data
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Request warning: {request.method} {request.path} - {response.status_code}",
                extra=log_data
            )
        else:
            logger.info(
                f"Request completed: {request.method} {request.path} - {response.status_code} ({log_data['duration_ms']}ms)",
                extra=log_data
            )

    def _get_client_ip(self):
        """获取客户端真实IP"""
        # 检查代理头
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr

    def _get_user_info(self):
        """获取当前用户信息"""
        try:
            # 尝试从JWT获取用户信息
            from flask_jwt import get_jwt_identity, current_user
            user_id = get_jwt_identity() if get_jwt_identity() else None
            return {
                'user_id': user_id,
                'username': getattr(current_user, 'username', None) if user_id else None
            }
        except Exception:
            # 未认证或认证失败
            return {'user_id': None, 'username': None}

    def _sanitize_body(self, body):
        """清理请求体中的敏感信息"""
        if not isinstance(body, dict):
            return body

        sensitive_fields = ['password', 'password_hash', 'api_key', 'secret', 'token']
        sanitized = body.copy()

        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***FILTERED***'

        return sanitized


def init_request_logging(app):
    """初始化请求日志中间件"""
    RequestLoggingMiddleware(app)
    app.logger.info("请求日志中间件已启用")
