"""
综合评分引擎

0-100 综合评分：基本面（50%）+ 估值（30%）+ 成长（20%）
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.services.analysis.fundamental import FundamentalAnalyzer
from app.services.analysis.valuation import ValuationAnalyzer
from app.services.analysis.dupont import DupontAnalyzer

logger = logging.getLogger(__name__)


class StockScorer:
    """股票综合评分器"""
    
    def __init__(self):
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.valuation_analyzer = ValuationAnalyzer()
        self.dupont_analyzer = DupontAnalyzer()
    
    def score(self, code: str) -> Dict[str, Any]:
        """
        综合评分（0-100）
        
        Args:
            code: 股票代码
        
        Returns:
            评分结果字典
        """
        try:
            # 获取各项分析结果
            fundamental = self.fundamental_analyzer.analyze(code)
            valuation = self.valuation_analyzer.analyze(code)
            dupont = self.dupont_analyzer.analyze(code)
            
            # 计算各维度评分
            fundamental_score = self._score_fundamental(fundamental)
            valuation_score = self._score_valuation(valuation)
            growth_score = self._score_growth(fundamental)
            
            # 加权综合评分
            total_score = (
                fundamental_score * 0.5 +
                valuation_score * 0.3 +
                growth_score * 0.2
            )
            
            # 评级映射
            rating = self._get_rating(total_score)
            
            result = {
                'code': fundamental.get('code', code),
                'total_score': round(total_score, 2),
                'rating': rating,
                'breakdown': {
                    'fundamental_score': round(fundamental_score, 2),
                    'valuation_score': round(valuation_score, 2),
                    'growth_score': round(growth_score, 2)
                },
                'weights': {
                    'fundamental': 0.5,
                    'valuation': 0.3,
                    'growth': 0.2
                },
                'details': {
                    'fundamental': fundamental,
                    'valuation': valuation,
                    'dupont': dupont
                },
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"综合评分失败: {code}, {e}")
            return {
                'code': code,
                'total_score': 0,
                'rating': 'D',
                'error': str(e),
                'breakdown': {},
                'weights': {}
            }
    
    def _score_fundamental(self, fundamental: Dict[str, Any]) -> float:
        """
        基本面评分（0-100）
        
        评估维度：
        - 盈利能力（40%）：ROE、毛利率、净利率
        - 偿债能力（30%）：资产负债率、流动比率
        - 运营效率（30%）：资产周转率
        """
        if not fundamental or fundamental.get('error'):
            return 50  # 默认中等分数
        
        score = 0
        weight_sum = 0
        
        # 盈利能力评分
        profitability = fundamental.get('profitability', {})
        if profitability:
            profit_score = 0
            profit_weight = 0
            
            # ROE 评分（权重 20）
            roe = profitability.get('roe')
            if roe is not None:
                if roe >= 20:
                    profit_score += 20
                elif roe >= 15:
                    profit_score += 16
                elif roe >= 10:
                    profit_score += 12
                elif roe >= 5:
                    profit_score += 8
                else:
                    profit_score += 4
                profit_weight += 20
            
            # 毛利率评分（权重 10）
            gross_margin = profitability.get('gross_margin')
            if gross_margin is not None:
                if gross_margin >= 50:
                    profit_score += 10
                elif gross_margin >= 30:
                    profit_score += 7
                elif gross_margin >= 20:
                    profit_score += 5
                else:
                    profit_score += 3
                profit_weight += 10
            
            # 净利率评分（权重 10）
            net_margin = profitability.get('net_margin')
            if net_margin is not None:
                if net_margin >= 20:
                    profit_score += 10
                elif net_margin >= 10:
                    profit_score += 7
                elif net_margin >= 5:
                    profit_score += 5
                else:
                    profit_score += 3
                profit_weight += 10
            
            if profit_weight > 0:
                score += (profit_score / profit_weight) * 40
                weight_sum += 40
        
        # 偿债能力评分
        solvency = fundamental.get('solvency', {})
        if solvency:
            solvency_score = 0
            solvency_weight = 0
            
            # 资产负债率（权重 15）
            debt_ratio = solvency.get('debt_to_assets')
            if debt_ratio is not None:
                if debt_ratio <= 40:
                    solvency_score += 15
                elif debt_ratio <= 60:
                    solvency_score += 12
                elif debt_ratio <= 70:
                    solvency_score += 8
                else:
                    solvency_score += 4
                solvency_weight += 15
            
            # 流动比率（权重 15）
            current_ratio = solvency.get('current_ratio')
            if current_ratio is not None:
                if current_ratio >= 2.0:
                    solvency_score += 15
                elif current_ratio >= 1.5:
                    solvency_score += 12
                elif current_ratio >= 1.0:
                    solvency_score += 8
                else:
                    solvency_score += 4
                solvency_weight += 15
            
            if solvency_weight > 0:
                score += (solvency_score / solvency_weight) * 30
                weight_sum += 30
        
        # 运营效率评分
        efficiency = fundamental.get('efficiency', {})
        if efficiency:
            efficiency_score = 0
            efficiency_weight = 0
            
            # 总资产周转率（权重 30）
            asset_turn = efficiency.get('assets_turn')
            if asset_turn is not None:
                if asset_turn >= 1.0:
                    efficiency_score += 30
                elif asset_turn >= 0.7:
                    efficiency_score += 22
                elif asset_turn >= 0.5:
                    efficiency_score += 15
                else:
                    efficiency_score += 8
                efficiency_weight += 30
            
            if efficiency_weight > 0:
                score += (efficiency_score / efficiency_weight) * 30
                weight_sum += 30
        
        if weight_sum > 0:
            return min(score, 100)
        return 50  # 默认中等
    
    def _score_valuation(self, valuation: Dict[str, Any]) -> float:
        """
        估值评分（0-100）
        
        评估维度：
        - PE 历史分位（50%）
        - PB 历史分位（30%）
        - PEG（20%）
        """
        if not valuation or valuation.get('error'):
            return 50
        
        score = 0
        weight_sum = 0
        
        # PE 历史分位评分
        percentile = valuation.get('historical_percentile', {})
        pe_percentile = percentile.get('pe_percentile')
        
        if pe_percentile is not None:
            # 分位越低，估值越低，评分越高
            if pe_percentile <= 20:
                pe_score = 50
            elif pe_percentile <= 40:
                pe_score = 40
            elif pe_percentile <= 60:
                pe_score = 30
            elif pe_percentile <= 80:
                pe_score = 20
            else:
                pe_score = 10
            score += pe_score
            weight_sum += 50
        
        # PB 历史分位评分
        pb_percentile = percentile.get('pb_percentile')
        
        if pb_percentile is not None:
            if pb_percentile <= 20:
                pb_score = 30
            elif pb_percentile <= 40:
                pb_score = 24
            elif pb_percentile <= 60:
                pb_score = 18
            elif pb_percentile <= 80:
                pb_score = 12
            else:
                pb_score = 6
            score += pb_score
            weight_sum += 30
        
        # PEG 评分
        peg = valuation.get('peg')
        
        if peg is not None:
            if peg < 0.5:
                peg_score = 20
            elif peg < 1.0:
                peg_score = 15
            elif peg < 1.5:
                peg_score = 10
            elif peg < 2.0:
                peg_score = 5
            else:
                peg_score = 0
            score += peg_score
            weight_sum += 20
        
        if weight_sum > 0:
            return min(score, 100)
        return 50
    
    def _score_growth(self, fundamental: Dict[str, Any]) -> float:
        """
        成长评分（0-100）
        
        评估维度：
        - 营收增速（40%）
        - 净利增速（40%）
        - 连续增长季度数（20%）
        """
        if not fundamental or fundamental.get('error'):
            return 50
        
        growth = fundamental.get('growth', {})
        if not growth:
            return 50
        
        score = 0
        weight_sum = 0
        
        # 营收增速评分
        revenue_yoy = growth.get('revenue_yoy')
        if revenue_yoy is not None:
            if revenue_yoy >= 30:
                rev_score = 40
            elif revenue_yoy >= 20:
                rev_score = 32
            elif revenue_yoy >= 10:
                rev_score = 24
            elif revenue_yoy >= 0:
                rev_score = 16
            else:
                rev_score = 8
            score += rev_score
            weight_sum += 40
        
        # 净利增速评分
        profit_yoy = growth.get('profit_yoy')
        if profit_yoy is not None:
            if profit_yoy >= 30:
                profit_score = 40
            elif profit_yoy >= 20:
                profit_score = 32
            elif profit_yoy >= 10:
                profit_score = 24
            elif profit_yoy >= 0:
                profit_score = 16
            else:
                profit_score = 8
            score += profit_score
            weight_sum += 40
        
        # 连续增长季度数评分
        revenue_continuous = growth.get('revenue_continuous_growth_quarters')
        profit_continuous = growth.get('profit_continuous_growth_quarters')
        
        avg_continuous = 0
        if revenue_continuous is not None and profit_continuous is not None:
            avg_continuous = (revenue_continuous + profit_continuous) / 2
        elif revenue_continuous is not None:
            avg_continuous = revenue_continuous
        elif profit_continuous is not None:
            avg_continuous = profit_continuous
        
        if avg_continuous > 0:
            if avg_continuous >= 6:
                continuous_score = 20
            elif avg_continuous >= 4:
                continuous_score = 15
            elif avg_continuous >= 2:
                continuous_score = 10
            else:
                continuous_score = 5
            score += continuous_score
            weight_sum += 20
        
        if weight_sum > 0:
            return min(score, 100)
        return 50
    
    def _get_rating(self, score: float) -> str:
        """评级映射"""
        if score >= 90:
            return "A+"
        elif score >= 75:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        else:
            return "D"


# 测试代码
if __name__ == '__main__':
    scorer = StockScorer()
    result = scorer.score('000001.SZ')
    
    print("=" * 60)
    print("平安银行 000001.SZ 综合评分")
    print("=" * 60)
    print(f"\n总评分: {result.get('total_score')}")
    print(f"评级: {result.get('rating')}")
    
    print("\n【分项评分】")
    breakdown = result.get('breakdown', {})
    for k, v in breakdown.items():
        print(f"  {k}: {v}")
    
    print("\n【权重配置】")
    weights = result.get('weights', {})
    for k, v in weights.items():
        print(f"  {k}: {v*100}%")
