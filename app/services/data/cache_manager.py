"""
缓存管理器

统一管理数据缓存策略，基于 Flask-Caching
"""
import logging
import hashlib
from functools import wraps
from flask import current_app

logger = logging.getLogger(__name__)


# 缓存时间配置（秒）
CACHE_TTL = {
    'quote': 30,          # 行情缓存 30s
    'kline': 300,         # K线缓存 5min
    'finance': 3600,      # 财务数据缓存 1h
    'stock_list': 86400,  # 股票列表缓存 24h
    'daily_basic': 60,    # 每日指标缓存 1min
    'chips': 1800,        # 筹码分布缓存 30min（数据每日18-19点更新，无需频繁拉取）
    'akshare': 60,        # AKShare 数据缓存 1min
    'score': 600,         # 综合评分缓存 10min
}


def _get_cache():
    """获取 Flask-Caching 实例"""
    try:
        from app.extensions import cache
        from flask import has_app_context
        # 只有在 Flask 应用上下文中才返回缓存实例
        if has_app_context():
            return cache
        return None
    except Exception:
        return None


def _make_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存 key"""
    parts = [prefix]
    for a in args:
        parts.append(str(a))
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}={v}")
    raw = ":".join(parts)
    if len(raw) > 200:
        raw = raw[:100] + ":" + hashlib.md5(raw.encode()).hexdigest()
    return raw


def cached(ttl_key: str = 'quote'):
    """
    缓存装饰器，自动使用预设 TTL

    Usage:
        @cached('kline')
        def get_kline(code, period='daily'):
            ...
    """
    timeout = CACHE_TTL.get(ttl_key, 300)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = _get_cache()
            cache_store = cache if cache is not None else cache_manager
            
            cache_key = _make_key(func.__module__, func.__name__, *args, **kwargs)
            result = cache_store.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result

            result = func(*args, **kwargs)
            try:
                cache_store.set(cache_key, result, timeout=timeout)
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")
            return result
        return wrapper
    return decorator


def invalidate(prefix: str = None):
    """清除缓存"""
    cache = _get_cache()
    if cache is None:
        return
    try:
        if prefix:
            # SimpleCache 不支持 pattern delete，清除全部
            cache.clear()
        else:
            cache.clear()
    except Exception as e:
        logger.warning(f"缓存清除失败: {e}")


def cache_get(key: str):
    """手动获取缓存"""
    cache = _get_cache()
    cache_store = cache if cache is not None else cache_manager
    return cache_store.get(key)


def cache_set(key: str, value, timeout: int = 300):
    """手动设置缓存"""
    cache = _get_cache()
    cache_store = cache if cache is not None else cache_manager
    try:
        cache_store.set(key, value, timeout=timeout)
    except Exception as e:
        logger.warning(f"缓存设置失败: {e}")


# 全局缓存管理器实例（供非 Flask 上下文使用）
class SimpleMemoryCache:
    """简单的内存缓存，用于脱离 Flask 上下文的场景"""

    def __init__(self):
        self._store = {}
        self._expiry = {}

    def get(self, key: str):
        import time
        if key in self._store:
            if time.time() < self._expiry.get(key, 0):
                return self._store[key]
            else:
                del self._store[key]
                del self._expiry[key]
        return None

    def set(self, key: str, value, timeout: int = 300):
        import time
        self._store[key] = value
        self._expiry[key] = time.time() + timeout

    def clear(self):
        self._store.clear()
        self._expiry.clear()


# 非 Flask 上下文的 fallback
_memory_cache = SimpleMemoryCache()


def get_cache_or_memory():
    """获取 Flask cache 或 fallback 到内存缓存"""
    cache = _get_cache()
    if cache is not None:
        try:
            # 测试是否在 Flask 上下文中
            cache.get('__test__')
            return cache
        except RuntimeError:
            pass
    return _memory_cache


cache_manager = SimpleMemoryCache()
