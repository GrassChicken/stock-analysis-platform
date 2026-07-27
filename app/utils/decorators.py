"""
API 错误处理器
统一处理 API 异常，确保返回格式一致
"""
from functools import wraps
import logging
from flask import jsonify, request
from app.utils.exceptions import APIError

logger = logging.getLogger(__name__)


def api_error_handler(f):
    """
    API 错误处理装饰器
    
    使用方式：
        @api_bp.route('/api/xxx')
        @api_error_handler
        def some_api():
            ...
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            # 业务异常 - 返回自定义错误码
            logger.warning(f"API 业务异常: {e.error_code} - {e.message}")
            response = {
                "success": False,
                "message": e.message,
                "error_code": e.error_code,
                "code": e.code
            }
            if e.details:
                response["details"] = e.details
            return jsonify(response), e.code
            
        except Exception as e:
            # 未预期的异常 - 记录详细日志
            logger.error(f"API 未预期异常: {str(e)}", exc_info=True)
            response = {
                "success": False,
                "message": "服务器内部错误",
                "error_code": "INTERNAL_ERROR",
                "code": 500
            }
            # 开发环境返回详细错误信息
            if request.environ.get('FLASK_ENV') == 'development':
                response["details"] = str(e)
            return jsonify(response), 500
            
    return wrapper


def validate_stock_code(code):
    """
    验证股票代码格式
    
    Args:
        code: 股票代码
        
    Returns:
        bool: 是否有效
        
    Raises:
        APIError: 股票代码格式无效
    """
    if not code:
        raise APIError("股票代码不能为空", 400, "INVALID_STOCK_CODE")
    
    # 股票代码格式验证（6位数字）
    if len(code) != 6 or not code.isdigit():
        raise APIError("股票代码格式无效，应为6位数字", 400, "INVALID_STOCK_CODE")
    
    return True
