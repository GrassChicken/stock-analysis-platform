"""应用配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """基础配置"""
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "stock-analysis-dev-key-change-in-prod")
    PORT = int(os.getenv("PORT", 5005))
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # 数据库
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'stock_analysis.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 缓存
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # 通达信
    TDX_SERVERS = os.getenv(
        "TDX_SERVERS", "119.147.212.81:7709,114.80.63.12:7709"
    ).split(",")

    # AI
    AI_API_BASE = os.getenv("AI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "qwen-plus")


class DevelopmentConfig(Config):
    """开发配置"""
    DEBUG = True
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300


class ProductionConfig(Config):
    """生产配置"""
    DEBUG = False
    CACHE_TYPE = "RedisCache"
    CACHE_DEFAULT_TIMEOUT = 600
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
