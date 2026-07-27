"""
统一异常定义
所有 API 错误都使用这些异常类，确保错误格式一致
"""

class APIError(Exception):
    """API 基础异常类"""
    def __init__(self, message, code=500, error_code=None, details=None):
        self.message = message
        self.code = code
        self.error_code = error_code or f"ERROR_{code}"
        self.details = details
        super().__init__(self.message)

class NotFoundError(APIError):
    """资源未找到"""
    def __init__(self, message="资源未找到", details=None):
        super().__init__(message, 404, "NOT_FOUND", details)

class ValidationError(APIError):
    """参数验证错误"""
    def __init__(self, message="参数验证失败", details=None):
        super().__init__(message, 400, "VALIDATION_ERROR", details)

class DataFetchError(APIError):
    """数据获取错误"""
    def __init__(self, message="数据获取失败", details=None):
        super().__init__(message, 500, "DATA_FETCH_ERROR", details)

class AnalysisError(APIError):
    """分析计算错误"""
    def __init__(self, message="分析计算失败", details=None):
        super().__init__(message, 500, "ANALYSIS_ERROR", details)

class CacheError(APIError):
    """缓存相关错误"""
    def __init__(self, message="缓存操作失败", details=None):
        super().__init__(message, 500, "CACHE_ERROR", details)
