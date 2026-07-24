"""资金面分析引擎

提供主力资金流向、北向资金、融资融券、筹码分布分析
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.services.data.akshare_client import akshare_client
from app.services.data.tushare_client import get_tushare_client

logger = logging.getLogger(__name__)


class CapitalAnalyzer:
    """资金面分析器"""

    def analyze(self, code: str) -> Dict[str, Any]:
        """
        完整资金面分析
        
        Args:
            code: 股票代码
        
        Returns:
            资金面分析结果
        """
        code = code.strip()
        if '.' in code:
            code = code.split('.')[0]
        
        result = {
            'code': code,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'money_flow': self._analyze_money_flow(code),
            'north_flow': self._analyze_north_flow(code),
            'margin': self._analyze_margin(code),
            'chip_distribution': self._analyze_chip_distribution(code),
            'capital_score': self._calc_capital_score(code),
        }
        
        return result

    def _analyze_money_flow(self, code: str) -> Dict[str, Any]:
        """分析主力资金流向"""
        flow_data = akshare_client.get_money_flow(code)
        
        if not flow_data:
            return {'available': False}
        
        # 判断主力动向
        main_net = flow_data.get('main_net_inflow', 0)
        trend = '流入' if main_net > 0 else '流出' if main_net < 0 else '平衡'
        
        # 计算主力净流入占比
        main_pct = flow_data.get('main_net_inflow_pct', 0)
        strength = '强' if abs(main_pct) > 5 else '中' if abs(main_pct) > 2 else '弱'
        
        return {
            'available': True,
            'date': flow_data.get('date'),
            'close': flow_data.get('close'),
            'change_pct': flow_data.get('change_pct'),
            'main_net_inflow': main_net,
            'main_net_inflow_pct': main_pct,
            'super_large_net': flow_data.get('super_large_net', 0),
            'large_net': flow_data.get('large_net', 0),
            'medium_net': flow_data.get('medium_net', 0),
            'small_net': flow_data.get('small_net', 0),
            'trend': trend,
            'strength': strength,
        }

    def _analyze_north_flow(self, code: str) -> Dict[str, Any]:
        """分析北向资金持股"""
        # 获取个股北向资金持股
        try:
            client = get_tushare_client()
            if not client.pro:
                return {'available': False}
            
            # 格式化代码
            ts_code = f"{code}.SH" if code.startswith('6') else f"{code}.SZ"
            
            # 获取沪深港通持股数据
            df = client.pro.hk_hold(ts_code=ts_code, start_date='', end_date='')
            
            if df is None or df.empty:
                return {'available': False}
            
            # 取最新数据
            latest = df.iloc[0]
            
            # 计算持股变化
            hold_ratio = latest.get('ratio', 0)
            
            return {
                'available': True,
                'date': str(latest.get('trade_date', '')),
                'hold_ratio': float(hold_ratio) if hold_ratio else 0,
                'hold_count': float(latest.get('count', 0)) if latest.get('count') else 0,
                'market': latest.get('market', ''),
            }
        except Exception as e:
            logger.warning(f"获取北向资金持股失败: {e}")
            return {'available': False}

    def _analyze_margin(self, code: str) -> Dict[str, Any]:
        """分析融资融券"""
        margin_data = akshare_client.get_margin_detail(code)
        
        if not margin_data:
            return {'available': False}
        
        # 计算融资融券趋势
        margin_balance = margin_data.get('融资余额', 0)
        margin_buy = margin_data.get('融资买入额', 0)
        margin_repay = margin_data.get('融资偿还额', 0)
        net_margin = margin_buy - margin_repay
        
        # 判断融资趋势
        trend = '增加' if net_margin > 0 else '减少' if net_margin < 0 else '平衡'
        
        return {
            'available': True,
            'date': margin_data.get('date'),
            'margin_balance': margin_balance,
            'margin_buy': margin_buy,
            'margin_repay': margin_repay,
            'net_margin': net_margin,
            'short_balance': margin_data.get('融券余额', 0),
            'trend': trend,
        }

    def _analyze_chip_distribution(self, code: str) -> Dict[str, Any]:
        """
        筹码分布估算
        
        基于成交量和价格波动估算获利盘/套牢盘比例
        """
        try:
            # 获取最近60天K线
            from app.services.data.stock_service import stock_service
            kline = stock_service.get_kline(code, period='daily', count=60)
            
            if not kline or len(kline) < 20:
                return {'available': False}
            
            # 当前价格
            current_price = kline[-1]['close']
            
            # 计算60日高低点
            high_60d = max(k['high'] for k in kline)
            low_60d = min(k['low'] for k in kline)
            
            # 估算获利盘比例（简化算法）
            # 假设筹码均匀分布，价格越高获利盘越多
            if high_60d > low_60d:
                profit_ratio = (current_price - low_60d) / (high_60d - low_60d) * 100
            else:
                profit_ratio = 50
            
            # 计算平均成本（成交量加权）
            total_amount = sum(k['amount'] for k in kline if k.get('amount'))
            total_volume = sum(k['vol'] for k in kline if k.get('vol'))
            avg_cost = total_amount / total_volume if total_volume > 0 else current_price
            
            # 判断筹码集中度
            price_range_pct = (high_60d - low_60d) / low_60d * 100
            concentration = '集中' if price_range_pct < 15 else '分散' if price_range_pct > 30 else '适中'
            
            return {
                'available': True,
                'current_price': current_price,
                'high_60d': high_60d,
                'low_60d': low_60d,
                'avg_cost': round(avg_cost, 2),
                'profit_ratio': round(profit_ratio, 2),
                'loss_ratio': round(100 - profit_ratio, 2),
                'concentration': concentration,
                'price_position': '高位' if current_price > avg_cost * 1.1 else '低位' if current_price < avg_cost * 0.9 else '中位',
            }
        except Exception as e:
            logger.warning(f"筹码分布分析失败: {e}")
            return {'available': False}

    def _calc_capital_score(self, code: str) -> Dict[str, Any]:
        """
        计算资金面评分
        
        评分维度：
        - 主力资金流向 (40分)
        - 北向资金持股 (30分)
        - 融资融券趋势 (30分)
        """
        score = 0
        details = {}
        
        # 1. 主力资金流向评分 (40分)
        flow_data = akshare_client.get_money_flow(code)
        if flow_data and flow_data.get('main_net_inflow') is not None:
            main_net = flow_data.get('main_net_inflow', 0)
            main_pct = flow_data.get('main_net_inflow_pct', 0)
            
            if main_net > 0:
                # 主力流入
                if main_pct > 5:
                    flow_score = 40
                elif main_pct > 2:
                    flow_score = 30
                elif main_pct > 0:
                    flow_score = 20
                else:
                    flow_score = 10
            else:
                # 主力流出
                if main_pct < -5:
                    flow_score = 0
                elif main_pct < -2:
                    flow_score = 5
                elif main_pct < 0:
                    flow_score = 10
                else:
                    flow_score = 15
            
            details['money_flow_score'] = flow_score
            details['money_flow_desc'] = f"主力净{'流入' if main_net > 0 else '流出'}{abs(main_net)/10000:.2f}万"
            score += flow_score
        
        # 2. 北向资金评分 (30分)
        try:
            client = get_tushare_client()
            if client.pro:
                ts_code = f"{code}.SH" if code.startswith('6') else f"{code}.SZ"
                df = client.pro.hk_hold(ts_code=ts_code, start_date='', end_date='')
                
                if df is not None and not df.empty:
                    hold_ratio = float(df.iloc[0].get('ratio', 0) or 0)
                    
                    # 北向资金持股比例评分
                    if hold_ratio > 5:
                        north_score = 30
                    elif hold_ratio > 3:
                        north_score = 25
                    elif hold_ratio > 1:
                        north_score = 20
                    elif hold_ratio > 0:
                        north_score = 10
                    else:
                        north_score = 0
                    
                    details['north_score'] = north_score
                    details['north_desc'] = f"北向持股{hold_ratio:.2f}%"
                    score += north_score
        except Exception as e:
            logger.warning(f"北向资金评分失败: {e}")
        
        # 3. 融资融券评分 (30分)
        margin_data = akshare_client.get_margin_detail(code)
        if margin_data:
            margin_balance = margin_data.get('融资余额', 0)
            net_margin = margin_data.get('融资买入额', 0) - margin_data.get('融资偿还额', 0)
            
            # 融资余额增加看多
            if net_margin > 0:
                margin_score = 25 if net_margin > 1000000 else 20 if net_margin > 0 else 15
            else:
                margin_score = 10 if net_margin > -1000000 else 5 if net_margin > -5000000 else 0
            
            details['margin_score'] = margin_score
            details['margin_desc'] = f"融资净{'买入' if net_margin > 0 else '偿还'}{abs(net_margin)/10000:.2f}万"
            score += margin_score
        
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
capital_analyzer = CapitalAnalyzer()
