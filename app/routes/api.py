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
from app.utils.decorators import api_error_handler, validate_stock_code
from app.utils.response import success_response, error_response
from app.utils.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


# ==================== 搜索 ====================

@api_bp.route("/search")
@api_error_handler
def search():
    """搜索股票"""
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        raise ValidationError("搜索关键词不能为空")
    
    try:
        results = stock_service.search_stock(keyword)[:20]
    except Exception as e:
        logger.error(f"搜索异常: {e}")
        raise
    
    # HTMX 请求返回 HTML
    if request.headers.get('HX-Request'):
        return render_template('partials/search_results.html', results=results)
    
    return jsonify({"results": results})


# ==================== 行情 ====================

@api_bp.route("/stock/<code>/quote")
@api_error_handler
def get_quote(code: str):
    """实时行情"""
    validate_stock_code(code)
    quote = stock_service.get_quote(code)
    if not quote:
        raise NotFoundError("未找到行情数据", details={"code": code})
    return jsonify(quote)


@api_bp.route("/stock/<code>/kline")
@api_error_handler
def get_kline(code: str):
    """K线数据"""
    validate_stock_code(code)
    period = request.args.get('period', 'daily')
    count = int(request.args.get('count', 120))
    kline = stock_service.get_kline(code, period=period, count=count)
    return jsonify({"code": code, "period": period, "data": kline})


@api_bp.route("/stock/<code>/daily_basic")
@api_error_handler
def get_daily_basic(code: str):
    """每日基本指标（PE/PB/市值等）"""
    validate_stock_code(code)
    data = stock_service.get_daily_basic(code)
    if not data:
        raise NotFoundError("未找到指标数据", details={"code": code})
    return jsonify(data)


@api_bp.route("/stock/<code>/chips")
@api_error_handler
def get_chips(code: str):
    """筹码分布（每日18-19点更新当日数据）"""
    validate_stock_code(code)
    data = stock_service.get_chips(code)
    # 无数据也返回 200，由前端根据 available 优雅提示
    return jsonify(data)


@api_bp.route("/stock/<code>/forecast")
@api_error_handler
def get_stock_forecast(code: str):
    """个股业绩预告（10000积分专属接口）"""
    validate_stock_code(code)
    data = stock_service.get_forecast(code)
    return jsonify(data)


@api_bp.route("/market/forecast")
@api_error_handler
def get_market_forecast():
    """全市场业绩预告（10000积分专属接口，支持筛选）"""
    forecast_type = request.args.get('type', '')  # 预增/预减/扭亏/首亏/续亏/续盈/略增/略减
    period = request.args.get('period', '')  # 报告期如 20241231
    start_date = request.args.get('start_date', '')  # 公告日期范围
    end_date = request.args.get('end_date', '')
    data = stock_service.get_market_forecast(
        forecast_type=forecast_type,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    return jsonify(data)


@api_bp.route("/stock/<code>/patterns")
@api_error_handler
def get_patterns(code: str):
    """K线形态标注（全量扫描，缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"patterns:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"形态标注缓存命中: {code}")
        return jsonify(cached_result)
    
    from app.services.data.stock_service import stock_service
    from app.services.analysis.technical import TechnicalAnalyzer
    
    # 获取K线数据（最近250根日K）
    kline = stock_service.get_kline(code, period='daily', count=250)
    if not kline:
        return jsonify({"patterns": [], "error": "K线数据为空"})
    
    analyzer = TechnicalAnalyzer()
    analyzer.kline_data = kline
    patterns = analyzer.detect_all_patterns(kline)
    
    result = {
        "code": code,
        "patterns": patterns,
        "total": len(patterns)
    }
    
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"形态标注已缓存: {code}, 共{len(patterns)}个")
    return jsonify(result)


# ==================== 分析 ====================

from app.extensions import cache as flask_cache

@api_bp.route("/stock/<code>/score")
@api_error_handler
def get_score(code: str):
    """综合评分（缓存5分钟）"""
    validate_stock_code(code)
    # 生成缓存键
    cache_key = f"score:{code}"
    
    # 尝试从缓存获取
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"评分缓存命中: {code}")
        return jsonify(cached_result)
    
    # 缓存未命中，执行计算
    scorer = StockScorer()
    result = scorer.score(code)
    
    # 存入缓存（5分钟 = 300秒）
    flask_cache.set(cache_key, result, timeout=600)
    logger.info(f"评分结果已缓存: {code}")
    
    return jsonify(result)


@api_bp.route("/stock/<code>/fundamental")
@api_error_handler
def get_fundamental(code: str):
    """基本面分析（缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"fundamental:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"基本面缓存命中: {code}")
        return jsonify(cached_result)
    
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze(code)
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"基本面结果已缓存: {code}")
    return jsonify(result)


@api_bp.route("/stock/<code>/valuation")
@api_error_handler
def get_valuation(code: str):
    """估值分析（缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"valuation:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"估值缓存命中: {code}")
        return jsonify(cached_result)
    
    analyzer = ValuationAnalyzer()
    result = analyzer.analyze(code)
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"估值结果已缓存: {code}")
    return jsonify(result)


@api_bp.route("/stock/<code>/dupont")
@api_error_handler
def get_dupont(code: str):
    """杜邦分析（缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"dupont:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"杜邦缓存命中: {code}")
        return jsonify(cached_result)
    
    analyzer = DupontAnalyzer()
    result = analyzer.analyze(code)
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"杜邦结果已缓存: {code}")
    return jsonify(result)


@api_bp.route("/stock/<code>/technical")
@api_error_handler
def get_technical(code: str):
    """技术面分析（缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"technical:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"技术面缓存命中: {code}")
        return jsonify(cached_result)
    
    analyzer = TechnicalAnalyzer()
    result = analyzer.analyze(code)
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"技术面结果已缓存: {code}")
    return jsonify(result)


@api_bp.route("/stock/<code>/capital")
@api_error_handler
def get_capital(code: str):
    """资金面分析（缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"capital:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"资金面缓存命中: {code}")
        return jsonify(cached_result)
    
    result = capital_analyzer.analyze(code)
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"资金面结果已缓存: {code}")
    return jsonify(result)


@api_bp.route("/stock/<code>/industry")
@api_error_handler
def get_industry(code: str):
    """行业面分析（缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"industry:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"行业面缓存命中: {code}")
        return jsonify(cached_result)
    
    result = industry_analyzer.analyze(code)
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"行业面结果已缓存: {code}")
    return jsonify(result)


@api_bp.route("/stock/<code>/ai")
@api_error_handler
def get_ai_analysis(code: str):
    """AI 智能分析（缓存1小时）"""
    validate_stock_code(code)
    cache_key = f"ai:{code}"
    cached_result = flask_cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"AI分析缓存命中: {code}")
        return jsonify(cached_result)
    
    from app.services.analysis.ai_analyzer import AIAnalyzer
    
    # 检查 API Key 是否配置
    import os
    api_key = os.getenv('AI_API_KEY')
    if not api_key:
        raise ValidationError("AI_API_KEY 未配置", details={"message": "请在 .env 文件中配置 AI_API_KEY"})
    
    # 获取六维评分数据
    scorer = StockScorer()
    score_data = scorer.score(code)
    
    if 'error' in score_data:
        raise ValidationError("评分数据获取失败", details={"error": score_data['error']})
    
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
    
    flask_cache.set(cache_key, result, timeout=3600)
    logger.debug(f"AI分析结果已缓存: {code}")
    
    return jsonify(result)


# ==================== 自选股 ====================

@api_bp.route("/watchlist", methods=['GET'])
@api_error_handler
def get_watchlist():
    """获取自选股列表（带实时行情）"""
    from app.models.database import Watchlist
    from app.extensions import db
    
    try:
        # 查询自选股列表
        items = Watchlist.query.order_by(Watchlist.created_at.desc()).all()
        
        if not items:
            # HTMX 请求返回 HTML
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
        
        # HTMX 请求返回 HTML
        if request.headers.get('HX-Request'):
            return render_template('partials/watchlist_items.html', items=watchlist_data)
        
        return jsonify({"watchlist": watchlist_data})
    except Exception as e:
        logger.error(f"获取自选股列表失败: {e}")
        # HTMX 请求返回 HTML 错误
        if request.headers.get('HX-Request'):
            return f'<p class="text-sm text-red-500 text-center py-4">加载失败: {str(e)}</p>'
        raise


@api_bp.route("/watchlist", methods=['POST'])
@api_error_handler
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
            raise ValidationError("股票代码不能为空")
        
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
        raise


@api_bp.route("/watchlist/<code>", methods=['DELETE'])
@api_error_handler
def remove_watchlist(code: str):
    """删除自选股"""
    from app.models.database import Watchlist
    from app.extensions import db
    
    try:
        validate_stock_code(code)
        item = Watchlist.query.filter_by(code=code).first()
        if not item:
            raise NotFoundError("未找到该自选股", details={"code": code})
        
        db.session.delete(item)
        db.session.commit()
        
        logger.info(f"删除自选股: {code}")
        return jsonify({"message": "已移除自选股", "code": code})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除自选股失败: {e}")
        raise


@api_bp.route("/watchlist/<code>/group", methods=['PUT'])
@api_error_handler
def update_watchlist_group(code: str):
    """修改自选股分组"""
    from app.models.database import Watchlist
    from app.extensions import db
    
    try:
        validate_stock_code(code)
        data = request.get_json() if request.is_json else request.form
        group_name = data.get('group', '').strip()
        
        if not group_name:
            raise ValidationError("分组名称不能为空")
        
        item = Watchlist.query.filter_by(code=code).first()
        if not item:
            raise NotFoundError("未找到该自选股", details={"code": code})
        
        old_group = item.group_name
        item.group_name = group_name
        db.session.commit()
        
        logger.info(f"修改自选股分组: {code} {old_group} -> {group_name}")
        return jsonify({
            "message": f"已移动到 {group_name}",
            "code": code,
            "old_group": old_group,
            "new_group": group_name
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"修改自选股分组失败: {e}")
        raise


@api_bp.route("/watchlist/groups", methods=['GET'])
@api_error_handler
def get_watchlist_groups():
    """获取所有分组列表"""
    from app.models.database import Watchlist
    from app.extensions import db
    
    try:
        # 查询所有不重复的分组
        groups = db.session.query(Watchlist.group_name).distinct().all()
        group_names = [g[0] for g in groups if g[0]]
        
        # 确保默认分组存在
        if '默认' not in group_names:
            group_names.insert(0, '默认')
        
        # 添加常用预设分组
        preset_groups = ['重点关注', '长线持有', '短线观察']
        for preset in preset_groups:
            if preset not in group_names:
                group_names.append(preset)
        
        return jsonify({"groups": group_names})
    except Exception as e:
        logger.error(f"获取分组列表失败: {e}")
        raise


# ==================== 对比 PK ====================

@api_bp.route("/compare", methods=['POST'])
@api_error_handler
def compare_stocks():
    """股票对比 PK"""
    from app.services.analysis.compare import compare_service
    data = request.get_json()
    codes = data.get('codes', [])

    if not codes or len(codes) < 2:
        raise ValidationError("至少选择 2 只股票", details={"received_count": len(codes) if codes else 0})

    result = compare_service.compare(codes)
    return jsonify(result)



# ==================== PDF 报告 ====================

@api_bp.route('/stock/<code>/report', methods=['GET'])
@api_error_handler
def generate_report(code: str):
    """生成 PDF 分析报告（缓存1天）"""
    import os
    from datetime import datetime
    from app.services.analysis.pdf_report import pdf_generator
    from app.services.analysis.scorer import StockScorer
    from app.services.data.stock_service import stock_service
    
    try:
        validate_stock_code(code)
        
        # 检查是否已有今日报告（缓存）
        reports_dir = '/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform/reports'
        today = datetime.now().strftime('%Y%m%d')
        cached_filename = f'report_{code}_{today}.pdf'
        cached_filepath = os.path.join(reports_dir, cached_filename)
        
        # 如果缓存存在，直接返回
        if os.path.exists(cached_filepath):
            logger.info(f"✓ PDF 报告缓存命中: {cached_filename}")
            return jsonify({
                'success': True, 
                'filepath': cached_filepath, 
                'filename': cached_filename,
                'cached': True
            })
        
        # 缓存未命中，生成新报告
        scorer = StockScorer()
        score_data = scorer.score(code)
        
        if 'error' in score_data:
            raise NotFoundError(f"无法获取股票评分数据: {score_data['error']}", details={"code": code})
        
        quote = stock_service.get_quote(code)
        
        if not quote:
            raise NotFoundError(f"未找到股票数据: {code}", details={"code": code})
        
        # 构建完整数据
        details = score_data.get('details', {})
        report_data = {
            'code': code,
            'name': quote.get('name', code),
            'score': score_data,
            'fundamental': details.get('fundamental', {}),
            'valuation': details.get('valuation', {}),
            'technical': details.get('technical', {}),
            'dupont': details.get('dupont', {}),
            'capital': details.get('capital', {}),
            'industry': details.get('industry', {}),
        }
        
        # 生成报告（使用带日期的文件名）
        os.makedirs(reports_dir, exist_ok=True)
        filepath = pdf_generator.generate_with_filename(report_data, cached_filepath)
        
        logger.info(f"✓ PDF 报告已生成并缓存: {cached_filename}")
        return jsonify({
            'success': True, 
            'filepath': filepath, 
            'filename': cached_filename,
            'cached': False
        })
    except Exception as e:
        logger.error(f"PDF 报告生成失败: {code}, {e}")
        raise


# ==================== PDF 下载 ====================

@api_bp.route('/reports/<filename>', methods=['GET'])
@api_error_handler
def download_report(filename: str):
    """下载 PDF 报告"""
    import os
    from flask import send_from_directory
    
    try:
        reports_dir = '/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform/reports'
        
        if not os.path.exists(os.path.join(reports_dir, filename)):
            raise NotFoundError(f"报告文件不存在: {filename}", details={"filename": filename})
        
        return send_from_directory(reports_dir, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"PDF 下载失败: {filename}, {e}")
        raise
