"""
Device ID utilities for multi-tenant isolation
"""
from flask import request
from functools import wraps


def get_device_id():
    """
    从请求头中提取 device_id

    Returns:
        str: Device ID，如果不存在则返回 None
    """
    device_id = request.headers.get('X-Device-ID')
    return device_id if device_id else None


def require_device_id(f):
    """
    装饰器：要求请求必须包含 device_id

    Usage:
        @app.route('/api/projects', methods=['POST'])
        @require_device_id
        def create_project():
            device_id = get_device_id()
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        device_id = get_device_id()
        if not device_id:
            from flask import jsonify
            return jsonify({
                'error': 'Device ID is required',
                'message': 'Please provide X-Device-ID header'
            }), 400
        return f(*args, **kwargs)
    return decorated_function
