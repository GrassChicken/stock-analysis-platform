"""API 路由 - JSON 数据接口 (供前端/HTMX调用)"""
from flask import Blueprint, jsonify, request, render_template
from app.services.data.stock_search import StockSearchService
from app.services.data.stock_service import stock_service
from app.services.analysis.fundamental import FundamentalAnalyzer
from app.services.analysis.valuation import ValuationAnalyzer
from app.services.analysis.dupont import DupontAnalyzer
from app.services.analysis.scorer import StockScorer
from app.services.analysis.technical import TechnicalAnalyzer

api_bp = Blueprint("api", __name__)


# ==================== 搜索 ====================

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
    
    if request.headers.get('HX-Request'):
        return render_template('partials/search_results.html', results=results)
    
    return jsonify({"results": results})


# ==================== 行情 ====================

@api_bp.route("/stock/<code>/quote")
def get_quote(code: str):
    """实时行情"""
    try:
        quote = stock_service.get_quote(code)
        if not quote:
            return jsonify({"error": "未找到行情数据"}), 404
        return jsonify(quote)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/kline")
def get_kline(code: str):
    """K线数据"""
    period = request.args.get('period', 'daily')
    count = int(request.args.get('count', 120))
    try:
        kline = stock_service.get_kline(code, period=period, count=count)
        return jsonify({"code": code, "period": period, "data": kline})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/daily_basic")
def get_daily_basic(code: str):
    """每日基本指标（PE/PB/市值等）"""
    try:
        data = stock_service.get_daily_basic(code)
        if not data:
            return jsonify({"error": "未找到指标数据"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 分析 ====================

@api_bp.route("/stock/<code>/score")
def get_score(code: str):
    """综合评分"""
    try:
        scorer = StockScorer()
        result = scorer.score(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/fundamental")
def get_fundamental(code: str):
    """基本面分析"""
    try:
        analyzer = FundamentalAnalyzer()
        result = analyzer.analyze(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/valuation")
def get_valuation(code: str):
    """估值分析"""
    try:
        analyzer = ValuationAnalyzer()
        result = analyzer.analyze(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/dupont")
def get_dupont(code: str):
    """杜邦分析"""
    try:
        analyzer = DupontAnalyzer()
        result = analyzer.analyze(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/technical")
def get_technical(code: str):
    """技术面分析"""
    try:
        analyzer = TechnicalAnalyzer()
        result = analyzer.analyze(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 自选股 ====================

@api_bp.route("/watchlist")
def get_watchlist():
    """自选股列表（暂用空列表）"""
    if request.headers.get('HX-Request'):
        return '<p class="text-sm text-gray-400 text-center py-4">暂无自选股，搜索添加</p>'
    return jsonify({"watchlist": []})
