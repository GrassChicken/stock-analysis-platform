"""
统一响应格式
所有 API 返回都使用这些函数，确保格式一致
"""
from flask import jsonify

def success_response(data=None, message="success", code=200):
    """
    成功响应格式
    {
        "success": true,
        "message": "success",
        "data": {...}
    }
    """
    response = {
        "success": True,
        "message": message,
        "code": code
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), code


def error_response(message, code=500, error_code=None, details=None):
    """
    错误响应格式
    {
        "success": false,
        "message": "error message",
        "code": 500,
        "error_code": "ERROR_CODE",
        "details": {...}
    }
    """
    response = {
        "success": False,
        "message": message,
        "code": code,
        "error_code": error_code or f"ERROR_{code}"
    }
    if details:
        response["details"] = details
    return jsonify(response), code


def not_found_response(message="资源未找到", details=None):
    """404 错误响应"""
    return error_response(message, 404, "NOT_FOUND", details)


def bad_request_response(message="请求参数错误", details=None):
    """400 错误响应"""
    return error_response(message, 400, "BAD_REQUEST", details)


def internal_error_response(message="服务器内部错误", details=None):
    """500 错误响应"""
    return error_response(message, 500, "INTERNAL_ERROR", details)
