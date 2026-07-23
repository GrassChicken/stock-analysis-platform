"""主路由 - 首页/搜索/自选股"""
from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """首页 - 搜索框 + 自选股列表"""
    return render_template("pages/index.html", title="智能股票深度分析")


@main_bp.route("/watchlist")
def watchlist():
    """自选股管理页"""
    return render_template("pages/watchlist.html", title="我的自选股")
