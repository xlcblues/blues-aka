import time
import uuid

from flask import jsonify, g, has_request_context

def create_response(data=None, status='success', message='Success', code=200, error_code=None):
    """创建响应体"""
    response_data = {
        'status': status,
        'code': code,
        'message': message,
        'data': data,
        'timestamp': int(time.time()),
    }

    if error_code:
        response_data['error_code'] = error_code

    response_data['request_id'] = get_request_id()

    response = jsonify(response_data)
    return response

def get_request_id():
    if has_request_context():
        if not hasattr(g, 'request_id'):
            g.request_id = str(uuid.uuid4())
        return g.request_id
    else:
        return str(uuid.uuid4())

def success(data=None, status='success', message='Success', code=200, error_code=None):
    """成功响应的快捷方法"""
    return create_response(data=data, status=status, message=message, code=code, error_code=error_code)

def error(data=None, status='error', message='Error', code=500, error_code=None):
    """成功响应的快捷方法"""
    return create_response(data=data, status=status, message=message, code=code, error_code=error_code)


