"""API 路由 - JSON 数据接口 (供 HTMX/图表调用)"""
from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__)


@api_bp.route("/search")
def search():
    """搜索股票"""
    # TODO: Phase 1 实现
    return jsonify({"results": [], "message": "搜索功能开发中"})


@api_bp.route("/stock/<code>/quote")
def get_quote(code: str):
    """实时行情"""
    # TODO: Phase 1 实现
    return jsonify({"code": code, "message": "行情接口开发中"})
