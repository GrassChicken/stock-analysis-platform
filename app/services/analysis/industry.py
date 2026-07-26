"""行业面分析引擎

提供行业分类、行业内排名、行业景气度、概念板块关联
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.data.tushare_client import get_tushare_client
from app.services.data.stock_service import stock_service

logger = logging.getLogger(__name__)


# 申万一级行业分类（简化版）
SW_INDUSTRY_MAP = {
    '银行': {'weight': 15, 'desc': '金融板块，低估值高分红'},
    '非银金融': {'weight': 12, 'desc': '券商保险，市场情绪指标'},
    '房地产': {'weight': 8, 'desc': '地产链，政策敏感型'},
    '食品饮料': {'weight': 20, 'desc': '消费龙头，稳定增长'},
    '医药生物': {'weight': 18, 'desc': '成长板块，创新药+医疗器械'},
    '电子': {'weight': 25, 'desc': '科技成长，半导体+消费电子'},
    '计算机': {'weight': 22, 'desc': '科技成长，软件+云计算'},
    '通信': {'weight': 20, 'desc': '科技成长，5G+光模块'},
    '传媒': {'weight': 15, 'desc': '内容产业，游戏+影视'},
    '电力设备': {'weight': 23, 'desc': '新能源，光伏+风电+储能'},
    '机械设备': {'weight': 18, 'desc': '高端制造，工业机器人'},
    '国防军工': {'weight': 20, 'desc': '军工装备，航天航空'},
    '汽车': {'weight': 16, 'desc': '新能源车+传统车企'},
    '家用电器': {'weight': 15, 'desc': '消费白马，全球化布局'},
    '轻工制造': {'weight': 12, 'desc': '家居建材，消费升级'},
    '纺织服饰': {'weight': 10, 'desc': '品牌消费，出口导向'},
    '美容护理': {'weight': 18, 'desc': '消费升级，医美+化妆品'},
    '商贸零售': {'weight': 14, 'desc': '消费渠道，电商+免税'},
    '社会服务': {'weight': 16, 'desc': '消费服务，旅游+教育'},
    '农林牧渔': {'weight': 12, 'desc': '周期板块，猪周期+种业'},
    '基础化工': {'weight': 15, 'desc': '周期板块，化工新材料'},
    '钢铁': {'weight': 10, 'desc': '周期板块，基建+地产'},
    '有色金属': {'weight': 18, 'desc': '周期板块，锂+铜+黄金'},
    '建筑材料': {'weight': 12, 'desc': '周期板块，水泥+玻璃'},
    '建筑装饰': {'weight': 10, 'desc': '基建链，央企估值修复'},
    '公用事业': {'weight': 12, 'desc': '防御板块，电力+环保'},
    '交通运输': {'weight': 14, 'desc': '基建链，航运+物流'},
    '煤炭': {'weight': 10, 'desc': '周期板块，高股息+能源安全'},
    '石油石化': {'weight': 12, 'desc': '能源板块，油气+炼化'},
    '环保': {'weight': 15, 'desc': '政策驱动，碳中和+污染治理'},
    '美容护理': {'weight': 18, 'desc': '消费升级，颜值经济'},
}


class IndustryAnalyzer:
    """行业面分析器"""

    def analyze(self, code: str, preloaded: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        完整行业面分析
        
        Args:
            code: 股票代码
            preloaded: 预加载数据字典（未使用，保持接口兼容）
        
        Returns:
            行业面分析结果
        """
        code = code.strip()
        if '.' in code:
            code = code.split('.')[0]
        
        # 缓存股票信息，避免重复查询
        stock_info = self._get_stock_info(code)
        self._stock_info_cache = stock_info
        self._daily_basic_cache = {}
        
        # 先执行同行对比，获取并缓存 peer_data
        peer_comparison = self._analyze_peer_comparison(code, stock_info)
        
        result = {
            'code': code,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'industry_info': self._analyze_industry(stock_info),
            'peer_comparison': peer_comparison,
            'industry_trend': self._analyze_industry_trend(stock_info),
            'concept_tags': self._get_concept_tags(code),
            # 将 peer_comparison 传递给评分方法，复用数据
            'industry_score': self._calc_industry_score(code, stock_info, peer_comparison),
        }
        
        # 清理缓存
        self._stock_info_cache = None
        self._daily_basic_cache = None
        
        return result

    def _get_stock_info(self, code: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            stocks = stock_service.get_all_stocks()
            for stock in stocks:
                if stock.get('code') == code or stock.get('ts_code', '').startswith(code):
                    return stock
        except Exception as e:
            logger.warning(f"获取股票信息失败: {e}")
        
        return {}

    def _analyze_industry(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析行业特征"""
        industry = stock_info.get('industry', '')
        
        if not industry:
            return {'available': False}
        
        # 获取行业特征
        industry_config = SW_INDUSTRY_MAP.get(industry, {})
        
        return {
            'available': True,
            'industry_name': industry,
            'industry_desc': industry_config.get('desc', '传统行业'),
            'industry_weight': industry_config.get('weight', 15),  # 平均关注度
            'market_position': '龙头' if stock_info.get('market') in ['主板', '创业板'] else '中小盘',
        }

    def _get_cached_daily_basic(self, ts_code: str) -> Dict[str, Any]:
        """获取 daily_basic 并缓存，避免重复调用"""
        if ts_code in self._daily_basic_cache:
            return self._daily_basic_cache[ts_code]
        
        daily_basic = stock_service.get_daily_basic(ts_code)
        self._daily_basic_cache[ts_code] = daily_basic
        return daily_basic

    def _analyze_peer_comparison(self, code: str, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        行业内对比分析
        
        获取同行业股票，计算相对排名
        """
        industry = stock_info.get('industry', '')
        if not industry:
            return {'available': False}
        
        try:
            # 获取同行业所有股票
            stocks = stock_service.get_all_stocks()
            peer_stocks = [s for s in stocks if s.get('industry') == industry]
            
            if len(peer_stocks) < 5:
                return {'available': False, 'reason': '同行股票太少'}
            
            # 获取关键指标（PE、PB、市值）
            peer_data = []
            for stock in peer_stocks[:10]:  # 限制到10只，减少API调用
                try:
                    ts_code = stock.get('ts_code', '')
                    if not ts_code:
                        continue
                    
                    daily_basic = self._get_cached_daily_basic(ts_code)
                    if daily_basic:
                        peer_data.append({
                            'code': stock.get('code'),
                            'name': stock.get('name'),
                            'pe': daily_basic.get('pe', 0),
                            'pb': daily_basic.get('pb', 0),
                            'total_mv': daily_basic.get('total_mv', 0),
                        })
                except Exception as e:
                    logger.warning(f"获取同行数据失败 {stock.get('code')}: {e}")
                    continue
            
            if not peer_data:
                return {'available': False}
            
            # 找当前股票的数据
            current = next((p for p in peer_data if p['code'] == code), None)
            if not current:
                return {'available': False}
            
            # 计算排名
            pe_rank = sum(1 for p in peer_data if 0 < p['pe'] < current['pe']) + 1
            pb_rank = sum(1 for p in peer_data if 0 < p['pb'] < current['pb']) + 1
            mv_rank = sum(1 for p in peer_data if p['total_mv'] > current['total_mv']) + 1
            
            return {
                'available': True,
                'peer_count': len(peer_data),
                'current': current,
                'pe_rank': pe_rank,
                'pb_rank': pb_rank,
                'mv_rank': mv_rank,
                'pe_percentile': round(pe_rank / len(peer_data) * 100, 1),
                'pb_percentile': round(pb_rank / len(peer_data) * 100, 1),
                'mv_percentile': round(mv_rank / len(peer_data) * 100, 1),
            }
        except Exception as e:
            logger.warning(f"同行对比分析失败: {e}")
            return {'available': False}

    def _analyze_industry_trend(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        行业趋势分析
        
        基于行业板块指数判断趋势
        """
        industry = stock_info.get('industry', '')
        if not industry:
            return {'available': False}
        
        # 简化版：基于行业特征给出趋势判断
        industry_config = SW_INDUSTRY_MAP.get(industry, {})
        weight = industry_config.get('weight', 15)
        
        if weight >= 20:
            trend = '热门'
            trend_desc = '市场关注度高，资金活跃'
        elif weight >= 15:
            trend = '稳定'
            trend_desc = '市场关注度中等，走势平稳'
        else:
            trend = '冷门'
            trend_desc = '市场关注度低，流动性一般'
        
        return {
            'available': True,
            'trend': trend,
            'trend_desc': trend_desc,
            'market_attention': weight,  # 市场关注度
        }

    def _get_concept_tags(self, code: str) -> Dict[str, Any]:
        """
        获取概念板块标签
        
        注：Tushare 免费接口暂不支持概念板块，这里用行业替代
        """
        stock_info = self._get_stock_info(code)
        industry = stock_info.get('industry', '')
        
        # 映射一些常见概念
        concept_map = {
            '电子': ['半导体', '芯片', '消费电子'],
            '计算机': ['云计算', '人工智能', '信创'],
            '通信': ['5G', '光模块', '通信设备'],
            '医药生物': ['创新药', '医疗器械', 'CXO'],
            '电力设备': ['光伏', '锂电池', '储能'],
            '食品饮料': ['白酒', '消费品', '内需'],
            '银行': ['高股息', '金融', '央企'],
            '房地产': ['地产链', '政策敏感'],
        }
        
        concepts = concept_map.get(industry, [industry]) if industry else []
        
        return {
            'available': len(concepts) > 0,
            'concepts': concepts,
            'industry': industry,
        }

    def _calc_industry_score(self, code: str, stock_info: Dict[str, Any], peer_comparison: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        计算行业面评分
        
        评分维度：
        - 行业热度 (40分)
        - 行业地位 (30分)
        - 行业趋势 (30分)
        """
        score = 0
        details = {}
        
        industry = stock_info.get('industry', '')
        if not industry:
            return {
                'total': 0,
                'rating': '未知',
                'details': {},
                'reason': '行业信息缺失'
            }
        
        # 1. 行业热度评分 (40分)
        industry_config = SW_INDUSTRY_MAP.get(industry, {})
        weight = industry_config.get('weight', 15)
        
        if weight >= 20:
            heat_score = 40
        elif weight >= 15:
            heat_score = 30
        elif weight >= 10:
            heat_score = 20
        else:
            heat_score = 10
        
        details['heat_score'] = heat_score
        details['heat_desc'] = f"{industry}行业热度{'高' if weight >= 20 else '中' if weight >= 15 else '低'}"
        score += heat_score
        
        # 2. 行业地位评分 (30分)
        # 复用 peer_comparison 的结果，不再重复遍历和API调用
        try:
            if peer_comparison and peer_comparison.get('available'):
                mv_rank = peer_comparison.get('mv_rank', 15)
            else:
                mv_rank = 15  # 默认中等
            
            # 排名越靠前分数越高
            if mv_rank <= 3:
                position_score = 30
            elif mv_rank <= 5:
                position_score = 25
            elif mv_rank <= 10:
                position_score = 20
            elif mv_rank <= 15:
                position_score = 15
            else:
                position_score = 10
            
            details['position_score'] = position_score
            details['position_desc'] = f"行业市值排名第{mv_rank}"
            score += position_score
        except Exception as e:
            logger.warning(f"行业地位评分失败: {e}")
            details['position_score'] = 15
            details['position_desc'] = '行业地位中等'
            score += 15
        
        # 3. 行业趋势评分 (30分)
        trend_weight = industry_config.get('weight', 15)
        if trend_weight >= 20:
            trend_score = 30
        elif trend_weight >= 15:
            trend_score = 20
        else:
            trend_score = 10
        
        details['trend_score'] = trend_score
        details['trend_desc'] = f"行业趋势{'向好' if trend_weight >= 20 else '平稳'}"
        score += trend_score
        
        # 评级
        if score >= 70:
            rating = '强势'
        elif score >= 50:
            rating = '偏多'
        elif score >= 30:
            rating = '中性'
        elif score >= 15:
            rating = '偏空'
        else:
            rating = '弱势'
        
        return {
            'total': score,
            'rating': rating,
            'details': details,
        }


# 全局实例
industry_analyzer = IndustryAnalyzer()
