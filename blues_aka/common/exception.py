class BaseException(Exception):
    """自定义异常基类"""
    def __init__(self, code, message, error_code):
        super.__init__()
        self.code = code
        self.message = message
        self.status_code = error_code

    def to_dict(self):
        return {'code': self.code, 'message': self.message, 'error_code': self.error_code}
