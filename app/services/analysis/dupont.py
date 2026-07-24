"""
杜邦分析引擎

ROE = 净利率 × 总资产周转率 × 权益乘数
"""
import logging
import time
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import tushare as ts
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 初始化 Tushare
load_dotenv('/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform/.env')
ts.set_token(os.getenv('TUSHARE_TOKEN'))
pro = ts.pro_api()


class DupontAnalyzer:
    """杜邦分析器"""
    
    def __init__(self):
        self.pro = pro
    
    def _format_code(self, code: str) -> str:
        """格式化股票代码"""
        code = code.strip()
        if '.' in code:
            return code.upper()
        if code.startswith(('6', '9')):
            return f"{code}.SH"
        return f"{code}.SZ"
    
    def _safe_round(self, value, decimals=2):
        """安全的四舍五入"""
        if value is None or pd.isna(value):
            return None
        try:
            return round(float(value), decimals)
        except:
            return None
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        杜邦分析
        
        Args:
            code: 股票代码
        
        Returns:
            杜邦分析结果字典
        """
        ts_code = self._format_code(code)
        logger.info(f"开始杜邦分析: {ts_code}")
        
        try:
            # 获取财务指标
            time.sleep(0.3)
            fina_df = self.pro.fina_indicator(ts_code=ts_code)
            
            if fina_df.empty:
                return {'code': ts_code, 'error': '无法获取财务数据'}
            
            # 杜邦分解（最近8个季度）
            periods_data = self._calculate_dupont_periods(fina_df)
            
            if not periods_data:
                return {'code': ts_code, 'error': '杜邦分解失败'}
            
            # 当前杜邦分解
            current = periods_data[0] if periods_data else {}
            
            # 趋势分析
            trend = self._analyze_trend(periods_data)
            
            # 各因素贡献度
            contribution = self._calculate_contribution(periods_data)
            
            result = {
                'code': ts_code,
                'current': {
                    'roe': current.get('roe'),
                    'net_profit_margin': current.get('net_margin'),
                    'asset_turnover': current.get('assets_turn'),
                    'equity_multiplier': current.get('equity_multiplier'),
                    'end_date': current.get('end_date')
                },
                'trend': trend,
                'contribution': contribution,
                'periods': periods_data[:4],  # 最近4期
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"✓ 杜邦分析完成: {ts_code}")
            return result
            
        except Exception as e:
            logger.error(f"杜邦分析失败: {ts_code}, {e}")
            return {
                'code': ts_code,
                'error': str(e),
                'current': {},
                'trend': {},
                'contribution': {}
            }
    
    def _calculate_dupont_periods(self, fina_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算多期杜邦分解"""
        periods = []
        
        try:
            # 取最近8期（2年）
            recent = fina_df.head(8)
            
            for _, row in recent.iterrows():
                end_date = row.get('end_date', '')
                
                # ROE
                roe = row.get('roe')
                
                # 净利率（%）
                net_margin = row.get('netprofit_margin')
                
                # 总资产周转率
                asset_turn = row.get('assets_turn')
                
                # 权益乘数 = 总资产 / 净资产
                # 从 fina_indicator 没有直接字段，需要计算
                # 权益乘数 = 1 / (1 - 资产负债率)
                debt_ratio = row.get('debt_to_assets')
                equity_multiplier = None
                if debt_ratio and debt_ratio < 100:
                    equity_multiplier = 100 / (100 - debt_ratio)
                
                period_data = {
                    'end_date': end_date,
                    'roe': self._safe_round(roe),
                    'net_margin': self._safe_round(net_margin),
                    'assets_turn': self._safe_round(asset_turn),
                    'equity_multiplier': self._safe_round(equity_multiplier)
                }
                
                # 验证：ROE ≈ 净利率 × 资产周转率 × 权益乘数
                if net_margin and asset_turn and equity_multiplier:
                    calculated_roe = (net_margin / 100) * asset_turn * equity_multiplier
                    period_data['roe_calculated'] = self._safe_round(calculated_roe)
                
                periods.append(period_data)
                
        except Exception as e:
            logger.error(f"计算杜邦分解失败: {e}")
        
        return periods
    
    def _analyze_trend(self, periods_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析各因素趋势"""
        if len(periods_data) < 2:
            return {}
        
        try:
            # 比较最新一期和上一期
            latest = periods_data[0]
            previous = periods_data[1]
            
            def get_change(key):
                val_latest = latest.get(key)
                val_prev = previous.get(key)
                if val_latest is not None and val_prev is not None:
                    change = val_latest - val_prev
                    return self._safe_round(change)
                return None
            
            def get_trend_direction(key):
                val_latest = latest.get(key)
                val_prev = previous.get(key)
                if val_latest is not None and val_prev is not None:
                    if val_latest > val_prev:
                        return "↑"
                    elif val_latest < val_prev:
                        return "↓"
                    else:
                        return "→"
                return "-"
            
            return {
                'roe_change': get_change('roe'),
                'roe_trend': get_trend_direction('roe'),
                'net_margin_change': get_change('net_margin'),
                'net_margin_trend': get_trend_direction('net_margin'),
                'asset_turn_change': get_change('assets_turn'),
                'asset_turn_trend': get_trend_direction('assets_turn'),
                'equity_multiplier_change': get_change('equity_multiplier'),
                'equity_multiplier_trend': get_trend_direction('equity_multiplier')
            }
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            return {}
    
    def _calculate_contribution(self, periods_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算各因素对 ROE 变化的贡献度"""
        if len(periods_data) < 2:
            return {}
        
        try:
            latest = periods_data[0]
            previous = periods_data[1]
            
            roe_latest = latest.get('roe')
            roe_prev = previous.get('roe')
            
            if roe_latest is None or roe_prev is None or roe_prev == 0:
                return {}
            
            roe_change = roe_latest - roe_prev
            
            # 简化贡献度分析（实际应该用连环替代法）
            net_margin_latest = latest.get('net_margin')
            net_margin_prev = previous.get('net_margin')
            asset_turn_latest = latest.get('assets_turn')
            asset_turn_prev = previous.get('assets_turn')
            equity_multiplier_latest = latest.get('equity_multiplier')
            equity_multiplier_prev = previous.get('equity_multiplier')
            
            # 估算各因素变化幅度
            changes = {}
            
            if net_margin_latest and net_margin_prev and net_margin_prev > 0:
                changes['net_margin_pct'] = self._safe_round((net_margin_latest - net_margin_prev) / net_margin_prev * 100)
            
            if asset_turn_latest and asset_turn_prev and asset_turn_prev > 0:
                changes['asset_turn_pct'] = self._safe_round((asset_turn_latest - asset_turn_prev) / asset_turn_prev * 100)
            
            if equity_multiplier_latest and equity_multiplier_prev and equity_multiplier_prev > 0:
                changes['equity_multiplier_pct'] = self._safe_round((equity_multiplier_latest - equity_multiplier_prev) / equity_multiplier_prev * 100)
            
            # 判断主要驱动因素
            main_driver = "无明显变化"
            if changes:
                max_key = max(changes, key=lambda k: abs(changes[k] or 0))
                main_driver_map = {
                    'net_margin_pct': '净利率提升' if changes[max_key] > 0 else '净利率下降',
                    'asset_turn_pct': '资产周转率提升' if changes[max_key] > 0 else '资产周转率下降',
                    'equity_multiplier_pct': '杠杆率提升' if changes[max_key] > 0 else '杠杆率下降'
                }
                main_driver = main_driver_map.get(max_key, main_driver)
            
            return {
                'roe_change': self._safe_round(roe_change),
                'changes': changes,
                'main_driver': main_driver
            }
        except Exception as e:
            logger.error(f"贡献度分析失败: {e}")
            return {}


# 测试代码
if __name__ == '__main__':
    analyzer = DupontAnalyzer()
    result = analyzer.analyze('000001.SZ')
    
    print("=" * 60)
    print("平安银行 000001.SZ 杜邦分析")
    print("=" * 60)
    
    print("\n【当前杜邦分解】")
    current = result.get('current', {})
    for k, v in current.items():
        print(f"  {k}: {v}")
    
    print("\n【趋势分析】")
    trend = result.get('trend', {})
    for k, v in trend.items():
        print(f"  {k}: {v}")
    
    print("\n【贡献度分析】")
    contribution = result.get('contribution', {})
    for k, v in contribution.items():
        print(f"  {k}: {v}")
    
    print("\n【历史期间】")
    periods = result.get('periods', [])
    for i, p in enumerate(periods[:3]):
        print(f"  第{i+1}期 ({p.get('end_date')}):")
        print(f"    ROE={p.get('roe')}%, 净利率={p.get('net_margin')}%, 周转率={p.get('assets_turn')}, 权益乘数={p.get('equity_multiplier')}")
