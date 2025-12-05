class BaseException(Exception):
    """自定义异常基类"""
    def __init__(self, code, message):
        super.__init__()
        self.code = code
        self.message = message

    def to_dict(self):
        return {'code': self.code, 'message': self.message}

class NotFoundError(BaseException):
    """资源未找到异常 (404)"""
    def __init__(self, code, message="资源未找到异常"):
        super().__init__(404, message)

class ValidationError(BaseException):
    """数据验证失败异常 (400)"""
    def __init__(self, code, message="数据验证失败异常"):
        super.__init__(400, message)

class InternalServerError(BaseException):
    """内部服务器错误 (500)"""
    def __init__(self, code, message="内部服务器错误"):
        super.__init__(500, message)