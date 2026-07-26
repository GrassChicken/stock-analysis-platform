"""Flask 应用工厂函数"""
import os
from flask import Flask
from app.config import Config, DevelopmentConfig, ProductionConfig
from app.extensions import db, cache


def create_app(config_class=None):
    """创建并配置 Flask 应用"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 根据环境变量选择配置类
    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            config_class = ProductionConfig
        else:
            config_class = DevelopmentConfig
    
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    cache.init_app(app)

    # 注册蓝图
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.analysis import analysis_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(analysis_bp)

    # 创建数据库表
    with app.app_context():
        from app.models.database import Watchlist, AnalysisReport
        db.create_all()

    # 健康检查路由
    @app.route("/api/health")
    def health():
        return {"status": "ok", "service": "stock-analysis-platform", "port": 5005}

    return app
