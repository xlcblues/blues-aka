import uuid
from flask import has_request_context, g


class BusinessException(Exception):
    """自定义异常基类"""

    def __init__(self, code, message, error_code, data=None):
        super().__init__()
        self.code = code
        self.message = message
        self.error_code = error_code
        self.data = data or {}

        # 自动生成 request_id
        if has_request_context():
            # 如果请求上下文中已有 request_id,则复用
            self.request_id = getattr(g, 'request_id', str(uuid.uuid4()))
        else:
            self.request_id = str(uuid.uuid4())

    def to_dict(self):
        return {
            'code': self.code,
            'message': self.message,
            'error_code': self.error_code,
            'request_id': self.request_id,
            'data': self.data
        }