"""API 路由 - JSON 数据接口 (供前端/HTMX调用)"""
import logging
from flask import Blueprint, jsonify, request, render_template
from app.services.data.stock_service import stock_service
from app.services.analysis.fundamental import FundamentalAnalyzer
from app.services.analysis.valuation import ValuationAnalyzer
from app.services.analysis.dupont import DupontAnalyzer
from app.services.analysis.scorer import StockScorer
from app.services.analysis.technical import TechnicalAnalyzer
from app.services.analysis.capital import capital_analyzer
from app.services.analysis.industry import industry_analyzer

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


# ==================== 搜索 ====================

@api_bp.route("/search")
def search():
    """搜索股票"""
    keyword = request.args.get('q', '').strip()
    
    # 调试：打印接收到的参数
    logger.info(f"搜索请求 - 原始关键词: {repr(keyword)}, 编码: {keyword.encode('utf-8')}")
    
    if not keyword:
        results = []
    else:
        try:
            # 尝试处理可能的编码问题
            try:
                # 如果是乱码（如 'å¹³å®'），尝试修复
                if keyword.isascii() and len(keyword) > 2:
                    # 可能被错误解码了，尝试重新编码
                    fixed = keyword.encode('latin-1').decode('utf-8')
                    if fixed != keyword:
                        logger.info(f"搜索请求 - 修复编码: {repr(keyword)} -> {repr(fixed)}")
                        keyword = fixed
            except:
                pass
            
            results = stock_service.search_stock(keyword)[:20]
            logger.info(f"搜索请求 - 返回结果数: {len(results)}")
        except Exception as e:
            logger.error(f"搜索异常: {e}")
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


@api_bp.route("/stock/<code>/capital")
def get_capital(code: str):
    """资金面分析"""
    try:
        result = capital_analyzer.analyze(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/industry")
def get_industry(code: str):
    """行业面分析"""
    try:
        result = industry_analyzer.analyze(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stock/<code>/ai")
def get_ai_analysis(code: str):
    """AI 智能分析"""
    try:
        from app.services.analysis.ai_analyzer import AIAnalyzer
        
        # 检查 API Key 是否配置
        import os
        api_key = os.getenv('AI_API_KEY')
        if not api_key:
            return jsonify({
                "error": "AI_API_KEY 未配置",
                "message": "请在 .env 文件中配置 AI_API_KEY"
            }), 500
        
        # 获取六维评分数据
        scorer = StockScorer()
        score_data = scorer.score(code)
        
        if 'error' in score_data:
            return jsonify({"error": score_data['error']}), 500
        
        # 构建 AI 分析数据
        ai_data = {
            'code': code,
            'total_score': score_data.get('total_score', 0),
            'rating': score_data.get('rating', ''),
            'breakdown': score_data.get('breakdown', {}),
            'weights': score_data.get('weights', {}),
            'fundamental': score_data.get('details', {}).get('fundamental', {}),
            'valuation': score_data.get('details', {}).get('valuation', {}),
            'technical': score_data.get('details', {}).get('technical', {}),
            'capital': score_data.get('details', {}).get('capital', {}),
            'industry': score_data.get('details', {}).get('industry', {})
        }
        
        # 调用 AI 分析
        analyzer = AIAnalyzer()
        result = analyzer.analyze(ai_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 自选股 ====================

@api_bp.route("/watchlist", methods=['GET'])
def get_watchlist():
    """获取自选股列表（带实时行情）"""
    from app.models.database import Watchlist
    from app.extensions import db
    
    try:
        # 查询自选股列表
        items = Watchlist.query.order_by(Watchlist.created_at.desc()).all()
        
        if not items:
            if request.headers.get('HX-Request'):
                return '<div class="text-center py-8"><p class="text-sm text-gray-400">暂无自选股</p><p class="text-xs text-gray-300 mt-1">搜索股票后点击 ⭐ 添加</p></div>'
            return jsonify({"watchlist": []})
        
        # 获取实时行情
        watchlist_data = []
        for item in items:
            try:
                quote = stock_service.get_quote(item.code)
                watchlist_data.append({
                    'code': item.code,
                    'name': item.name or quote.get('name', ''),
                    'price': quote.get('price', 0),
                    'change': quote.get('change', 0),
                    'change_pct': quote.get('change_pct', 0),
                    'group': item.group_name,
                    'created_at': item.created_at.strftime('%Y-%m-%d %H:%M') if item.created_at else ''
                })
            except Exception as e:
                logger.warning(f"获取自选股 {item.code} 行情失败: {e}")
                watchlist_data.append({
                    'code': item.code,
                    'name': item.name or item.code,
                    'price': 0,
                    'change': 0,
                    'change_pct': 0,
                    'group': item.group_name,
                    'created_at': item.created_at.strftime('%Y-%m-%d %H:%M') if item.created_at else ''
                })
        
        if request.headers.get('HX-Request'):
            return render_template('partials/watchlist_items.html', items=watchlist_data)
        
        return jsonify({"watchlist": watchlist_data})
    except Exception as e:
        logger.error(f"获取自选股列表失败: {e}")
        if request.headers.get('HX-Request'):
            return f'<p class="text-sm text-red-500 text-center py-4">加载失败: {str(e)}</p>'
        return jsonify({"error": str(e)}), 500


@api_bp.route("/watchlist", methods=['POST'])
def add_watchlist():
    """添加自选股"""
    from app.models.database import Watchlist
    from app.extensions import db
    
    try:
        data = request.get_json() if request.is_json else request.form
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        group_name = data.get('group', '默认')
        
        if not code:
            return jsonify({"error": "股票代码不能为空"}), 400
        
        # 检查是否已存在
        existing = Watchlist.query.filter_by(code=code).first()
        if existing:
            return jsonify({"message": "已在自选股中", "code": code}), 200
        
        # 创建新记录
        item = Watchlist(code=code, name=name, group_name=group_name)
        db.session.add(item)
        db.session.commit()
        
        logger.info(f"添加自选股: {code} {name}")
        return jsonify({"message": "已添加自选股", "code": code, "name": name}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加自选股失败: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/watchlist/<code>", methods=['DELETE'])
def remove_watchlist(code: str):
    """删除自选股"""
    from app.models.database import Watchlist
    from app.extensions import db
    
    try:
        item = Watchlist.query.filter_by(code=code).first()
        if not item:
            return jsonify({"error": "未找到该自选股"}), 404
        
        db.session.delete(item)
        db.session.commit()
        
        logger.info(f"删除自选股: {code}")
        return jsonify({"message": "已移除自选股", "code": code}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除自选股失败: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== 对比 PK ====================

@api_bp.route("/compare", methods=['POST'])
def compare_stocks():
    """股票对比 PK"""
    try:
        from app.services.analysis.compare import compare_service
        data = request.get_json()
        codes = data.get('codes', [])

        if not codes or len(codes) < 2:
            return jsonify({"error": "至少选择 2 只股票"}), 400

        result = compare_service.compare(codes)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

