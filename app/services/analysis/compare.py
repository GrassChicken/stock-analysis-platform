"""
对比分析服务

支持多只股票横向对比，输出结构化对比数据
"""
import logging
from typing import Dict, List, Any
from app.services.analysis.scorer import StockScorer
from app.services.data.stock_service import stock_service

logger = logging.getLogger(__name__)


class CompareService:
    """对比分析服务"""
    
    def __init__(self):
        self.scorer = StockScorer()
    
    def compare(self, codes: List[str]) -> Dict[str, Any]:
        """
        对比多只股票
        
        Args:
            codes: 股票代码列表 (2-4 只)
        
        Returns:
            对比数据
        """
        if not codes or len(codes) < 2:
            return {"error": "至少选择 2 只股票进行对比"}
        
        if len(codes) > 4:
            codes = codes[:4]
        
        results = []
        for code in codes:
            try:
                # 获取综合评分
                score_data = self.scorer.score(code)
                
                # 获取行情
                quote = stock_service.get_quote(code)
                
                # 获取每日指标
                daily = stock_service.get_daily_basic(code)
                
                # 构建对比条目
                item = {
                    'code': code,
                    'name': quote.get('name', code),
                    'price': quote.get('price', 0),
                    'change_pct': quote.get('change_pct', 0),
                    'total_score': score_data.get('total_score', 0),
                    'rating': score_data.get('rating', '--'),
                    'breakdown': score_data.get('breakdown', {}),
                    'valuation': {},
                    'fundamental': {},
                }
                
                # 从评分详情中提取数据
                details = score_data.get('details', {})
                
                # 估值数据
                valuation = details.get('valuation', {})
                current_val = valuation.get('current_valuation', {})
                item['valuation'] = {
                    'pe': current_val.get('pe', 0),
                    'pe_ttm': current_val.get('pe_ttm', 0),
                    'pb': current_val.get('pb', 0),
                    'ps': current_val.get('ps', 0),
                    'total_mv': current_val.get('total_mv', 0),
                    'circ_mv': current_val.get('circ_mv', 0),
                    'pe_percentile': valuation.get('historical_percentile', {}).get('pe_percentile', 0),
                    'pb_percentile': valuation.get('historical_percentile', {}).get('pb_percentile', 0),
                }
                
                # 基本面数据
                fundamental = details.get('fundamental', {})
                item['fundamental'] = {
                    'roe': fundamental.get('profitability', {}).get('roe', 0),
                    'net_margin': fundamental.get('profitability', {}).get('net_margin', 0),
                    'gross_margin': fundamental.get('profitability', {}).get('gross_margin', 0),
                    'revenue_yoy': fundamental.get('growth', {}).get('revenue_yoy', 0),
                    'profit_yoy': fundamental.get('growth', {}).get('profit_yoy', 0),
                    'debt_ratio': fundamental.get('solvency', {}).get('debt_to_assets', 0),
                }
                
                results.append(item)
                
            except Exception as e:
                logger.error(f"对比分析失败 {code}: {e}")
                results.append({
                    'code': code,
                    'name': code,
                    'error': str(e)
                })
        
        # 找出各维度最优
        comparison = {
            'stocks': results,
            'best': self._find_best(results),
            'summary': self._generate_summary(results)
        }
        
        return comparison
    
    def _find_best(self, stocks: List[Dict]) -> Dict[str, str]:
        """找出各维度最优的股票代码"""
        best = {}
        
        valid_stocks = [s for s in stocks if not s.get('error')]
        if not valid_stocks:
            return best
        
        # 综合评分最优
        best['total_score'] = max(valid_stocks, key=lambda x: x.get('total_score', 0)).get('code')
        
        # 各子维度最优
        dimensions = ['fundamental_score', 'technical_score', 'valuation_score', 
                      'capital_score', 'industry_score', 'growth_score']
        for dim in dimensions:
            best[dim] = max(valid_stocks, key=lambda x: x.get('breakdown', {}).get(dim, 0)).get('code')
        
        # 基本面指标最优
        best['roe'] = max(valid_stocks, key=lambda x: x.get('fundamental', {}).get('roe', 0) or 0).get('code')
        best['revenue_yoy'] = max(valid_stocks, key=lambda x: x.get('fundamental', {}).get('revenue_yoy', 0) or 0).get('code')
        
        # 估值最低 (PE 越低越好，但要排除负数)
        pe_valid = [s for s in valid_stocks if 0 < (s.get('valuation', {}).get('pe_ttm', 0) or 0) < 1000]
        if pe_valid:
            best['pe_ttm'] = min(pe_valid, key=lambda x: x.get('valuation', {}).get('pe_ttm', 999)).get('code')
        
        return best
    
    def _generate_summary(self, stocks: List[Dict]) -> str:
        """生成对比总结"""
        valid_stocks = [s for s in stocks if not s.get('error')]
        if not valid_stocks:
            return "无法生成对比总结"
        
        # 找出综合评分最高
        best = max(valid_stocks, key=lambda x: x.get('total_score', 0))
        names = [s.get('name', s.get('code')) for s in valid_stocks]
        
        summary = f"在 {'、'.join(names)} 中，{best.get('name')} 综合评分最高 ({best.get('total_score', 0):.1f} 分，评级 {best.get('rating', '--')})。"
        
        # 分析各维度亮点
        highlights = []
        breakdown = best.get('breakdown', {})
        
        if breakdown.get('fundamental_score', 0) >= 70:
            highlights.append(f"{best.get('name')}基本面优秀")
        if breakdown.get('technical_score', 0) >= 70:
            highlights.append(f"{best.get('name')}技术面强势")
        if breakdown.get('valuation_score', 0) >= 70:
            highlights.append(f"{best.get('name')}估值合理")
        
        if highlights:
            summary += f" {', '.join(highlights)}。"
        
        return summary


# 全局单例
compare_service = CompareService()
