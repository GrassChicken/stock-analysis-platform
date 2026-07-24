"""API 路由 - JSON 数据接口 (供 HTMX/图表调用)"""
from flask import Blueprint, jsonify, request, render_template
from app.services.data.stock_search import StockSearchService

api_bp = Blueprint("api", __name__)


@api_bp.route("/search")
def search():
    """搜索股票"""
    keyword = request.args.get('q', '').strip()
    if not keyword:
        results = []
    else:
        try:
            search_service = StockSearchService()
            results = search_service.search(keyword, limit=20)
        except Exception as e:
            if request.headers.get('HX-Request'):
                return f'<div class="text-center py-4 text-red-500">搜索失败: {str(e)}</div>'
            return jsonify({"results": [], "error": str(e)})
    
    # HTMX 请求返回 HTML 片段
    if request.headers.get('HX-Request'):
        return render_template('partials/search_results.html', results=results)
    
    # 普通请求返回 JSON
    return jsonify({"results": results})


@api_bp.route("/stock/<code>/quote")
def get_quote(code: str):
    """实时行情"""
    # TODO: Phase 1 实现
    return jsonify({"code": code, "message": "行情接口开发中"})
