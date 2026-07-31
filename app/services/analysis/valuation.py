"""
估值分析引擎

PE/PB/PS/PEG 分析 + 历史分位 + DCF 简化估值 + 估值评级
"""
import logging
import time
import math
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from app.services.data.tushare_client import get_tushare_client

logger = logging.getLogger(__name__)


class ValuationAnalyzer:
    """估值分析器"""
    
    def __init__(self):
        self.pro = get_tushare_client().pro
        self.discount_rate = 0.10  # 折现率 10%
        self.terminal_growth_rate = 0.03  # 永续增长率 3%
    
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
        if value is None or pd.isna(value) or math.isinf(value):
            return None
        try:
            return round(float(value), decimals)
        except:
            return None
    
    def _calculate_percentile(self, current: float, history: list) -> Optional[float]:
        """
        计算当前值在历史数据中的百分位（0-100）
        
        Args:
            current: 当前值
            history: 历史数据列表
        
        Returns:
            百分位数（0-100）
        """
        if not history or current is None:
            return None
        
        history_clean = [x for x in history if x is not None and not math.isnan(x) and x > 0]
        
        if not history_clean:
            return None
        
        below_count = sum(1 for x in history_clean if x < current)
        percentile = (below_count / len(history_clean)) * 100
        
        return round(percentile, 2)
    
    def analyze(self, code: str, preloaded: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        估值分析
        
        Args:
            code: 股票代码
            preloaded: 预加载数据字典（来自 DataCollector），含 daily_basic_df/fina_df/daily_df/income_df/balance_df
        
        Returns:
            估值分析结果字典
        """
        ts_code = self._format_code(code)
        logger.info(f"开始估值分析: {ts_code}")
        
        try:
            # 使用预加载数据或自行获取
            if preloaded:
                daily_basic_df = preloaded.get('daily_basic_df', pd.DataFrame())
                fina_df = preloaded.get('fina_df', pd.DataFrame())
                daily_df = preloaded.get('daily_df', pd.DataFrame())
                income_df = preloaded.get('income_df', pd.DataFrame())
                balance_df = preloaded.get('balance_df', pd.DataFrame())
            else:
                # 获取每日指标（PE/PB/PS）
                time.sleep(0.3)
                daily_basic_df = self.pro.daily_basic(ts_code=ts_code)
                
                # 获取财务指标（用于 PEG 和 DCF）
                time.sleep(0.3)
                fina_df = self.pro.fina_indicator(ts_code=ts_code)
                
                # 获取日线行情（当前价格）
                time.sleep(0.3)
                daily_df = self.pro.daily(ts_code=ts_code, start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
                
                # 获取利润表（用于 DCF）
                time.sleep(0.3)
                income_df = self.pro.income(ts_code=ts_code)
                
                # 获取资产负债表
                time.sleep(0.3)
                balance_df = self.pro.balancesheet(ts_code=ts_code)
            
            # 当前估值指标
            current_valuation = self._get_current_valuation(daily_basic_df, daily_df)
            
            # PE/PB 历史分位（近5年）
            historical_percentile = self._calculate_historical_percentile(daily_basic_df)
            
            # PEG
            peg = self._calculate_peg(current_valuation, fina_df)
            
            # DCF 简化估值
            dcf_valuation = self._calculate_dcf(fina_df, income_df, balance_df, daily_basic_df)
            
            # 估值评级
            rating = self._get_valuation_rating(historical_percentile, peg)
            
            result = {
                'code': ts_code,
                'current_valuation': current_valuation,
                'historical_percentile': historical_percentile,
                'peg': peg,
                'dcf_valuation': dcf_valuation,
                'rating': rating,
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"✓ 估值分析完成: {ts_code}")
            return result
            
        except Exception as e:
            logger.error(f"估值分析失败: {ts_code}, {e}")
            return {
                'code': ts_code,
                'error': str(e),
                'current_valuation': {},
                'historical_percentile': {},
                'peg': None,
                'dcf_valuation': {},
                'rating': '未知'
            }
    
    def _get_current_valuation(self, daily_basic_df: pd.DataFrame, daily_df: pd.DataFrame) -> Dict[str, Any]:
        """获取当前估值指标"""
        if daily_basic_df.empty:
            return {}
        
        try:
            latest = daily_basic_df.iloc[0]
            
            # 当前价格
            current_price = None
            if not daily_df.empty:
                current_price = daily_df.iloc[0]['close']
            else:
                # 尝试从 daily_basic 获取
                total_mv = latest.get('total_mv')
                total_share = latest.get('total_share')
                if total_mv and total_share:
                    current_price = (total_mv * 10000) / (total_share * 10000)  # 万元转元
            
            return {
                'price': self._safe_round(current_price),
                'pe': self._safe_round(latest.get('pe')),
                'pe_ttm': self._safe_round(latest.get('pe_ttm')),
                'pb': self._safe_round(latest.get('pb')),
                'ps': self._safe_round(latest.get('ps')),
                'ps_ttm': self._safe_round(latest.get('ps_ttm')),
                'dv_ratio': self._safe_round(latest.get('dv_ratio')),  # 股息率
                'total_mv': self._safe_round(latest.get('total_mv') / 10000) if latest.get('total_mv') else None,  # 亿元
                'circ_mv': self._safe_round(latest.get('circ_mv') / 10000) if latest.get('circ_mv') else None,  # 亿元
                'turnover_rate': self._safe_round(latest.get('turnover_rate')),  # 换手率
            }
        except Exception as e:
            logger.error(f"获取当前估值指标失败: {e}")
            return {}
    
    def _calculate_historical_percentile(self, daily_basic_df: pd.DataFrame) -> Dict[str, Any]:
        """计算 PE/PB 历史分位（近5年）"""
        if daily_basic_df.empty:
            return {}
        
        try:
            # 筛选近5年数据
            five_years_ago = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
            
            # 按日期筛选（假设 trade_date 格式为 YYYYMMDD）
            history_df = daily_basic_df[daily_basic_df['trade_date'] >= five_years_ago].copy()
            
            if history_df.empty:
                history_df = daily_basic_df.copy()  # 如果不足5年，用全部数据
            
            # 提取 PE 和 PB 历史数据
            pe_history = history_df['pe_ttm'].dropna().tolist()
            pb_history = history_df['pb'].dropna().tolist()
            
            # 当前值
            current_pe = history_df.iloc[0]['pe_ttm'] if 'pe_ttm' in history_df.columns else None
            current_pb = history_df.iloc[0]['pb'] if 'pb' in history_df.columns else None
            
            # 计算百分位
            pe_percentile = self._calculate_percentile(current_pe, pe_history)
            pb_percentile = self._calculate_percentile(current_pb, pb_history)
            
            # PE/PB 历史均值
            pe_mean = self._safe_round(np.mean(pe_history)) if pe_history else None
            pb_mean = self._safe_round(np.mean(pb_history)) if pb_history else None
            
            return {
                'pe_percentile': pe_percentile,  # 0-100
                'pb_percentile': pb_percentile,  # 0-100
                'pe_mean': pe_mean,
                'pb_mean': pb_mean,
                'pe_current': self._safe_round(current_pe),
                'pb_current': self._safe_round(current_pb),
                'data_years': len(history_df['trade_date'].unique()) // 250  # 估算年份
            }
        except Exception as e:
            logger.error(f"计算历史分位失败: {e}")
            return {}
    
    def _calculate_peg(self, current_valuation: Dict[str, Any], fina_df: pd.DataFrame) -> Optional[float]:
        """
        计算 PEG = PE / 净利增速
        
        PEG < 1: 低估
        PEG = 1: 合理
        PEG > 1: 高估
        """
        if not current_valuation or fina_df.empty:
            return None
        
        try:
            pe_ttm = current_valuation.get('pe_ttm')
            
            if not pe_ttm or pe_ttm <= 0:
                return None
            
            # 取最近一期的净利增速
            profit_growth = fina_df.iloc[0].get('dt_netprofit_yoy')
            
            if profit_growth is None or profit_growth <= 0:
                return None
            
            peg = pe_ttm / profit_growth
            
            return self._safe_round(peg)
        except Exception as e:
            logger.error(f"计算 PEG 失败: {e}")
            return None
    
    def _calculate_dcf(self, fina_df: pd.DataFrame, income_df: pd.DataFrame, 
                       balance_df: pd.DataFrame, daily_basic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        DCF 简化估值（三阶段模型）
        
        阶段1：高增长期（1-5年），增速 20%
        阶段2：稳定期（6-10年），增速 10%
        阶段3：永续期（11年+），增速 3%
        
        折现率：10%
        """
        if fina_df.empty or income_df.empty or balance_df.empty:
            return {}
        
        try:
            # 基础数据
            latest_income = income_df.iloc[0]
            latest_balance = balance_df.iloc[0]
            latest_fina = fina_df.iloc[0]
            
            # 当前自由现金流（FCF）
            # 简化计算：经营现金流 - 资本支出
            # 如果没有现金流数据，用净利润近似
            net_profit = latest_income.get('n_income_attr_p')
            
            if not net_profit or net_profit <= 0:
                return {}
            
            # 初始 FCF = 净利润 * 0.8（近似）
            initial_fcf = net_profit * 0.8
            
            # 增长率设定
            growth_rate_1 = 0.20  # 前5年 20%
            growth_rate_2 = 0.10  # 6-10年 10%
            terminal_growth = self.terminal_growth_rate  # 永续 3%
            
            discount_rate = self.discount_rate  # 10%
            
            # 计算未来10年 FCF 现值
            pv_fcf = 0
            fcf = initial_fcf
            
            # 阶段1：1-5年
            for year in range(1, 6):
                fcf *= (1 + growth_rate_1)
                pv = fcf / ((1 + discount_rate) ** year)
                pv_fcf += pv
            
            # 阶段2：6-10年
            for year in range(6, 11):
                fcf *= (1 + growth_rate_2)
                pv = fcf / ((1 + discount_rate) ** year)
                pv_fcf += pv
            
            # 阶段3：永续价值（第10年末）
            terminal_value = (fcf * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            pv_terminal = terminal_value / ((1 + discount_rate) ** 10)
            
            # 企业价值 = FCF 现值 + 永续价值现值
            enterprise_value = pv_fcf + pv_terminal
            
            # 股权价值 = 企业价值 + 现金 - 负债
            # 简化：假设净现金 = 0
            equity_value = enterprise_value
            
            # 每股价值
            total_share = daily_basic_df.iloc[0].get('total_share') if not daily_basic_df.empty else None
            
            if total_share:
                per_share_value = equity_value / (total_share * 10000)  # total_share 单位：万股
            else:
                per_share_value = None
            
            return {
                'enterprise_value': self._safe_round(enterprise_value / 100000000),  # 亿元
                'equity_value': self._safe_round(equity_value / 100000000),  # 亿元
                'per_share_value': self._safe_round(per_share_value),  # 元/股
                'initial_fcf': self._safe_round(initial_fcf / 100000000),  # 亿元
                'discount_rate': discount_rate * 100,  # 百分比
                'terminal_growth_rate': terminal_growth * 100  # 百分比
            }
        except Exception as e:
            logger.error(f"DCF 估值失败: {e}")
            return {}
    
    def _get_valuation_rating(self, historical_percentile: Dict[str, Any], peg: Optional[float]) -> str:
        """
        估值评级
        
        综合考虑 PE/PB 历史分位和 PEG
        """
        try:
            pe_percentile = historical_percentile.get('pe_percentile')
            pb_percentile = historical_percentile.get('pb_percentile')
            
            # 综合分位（PE 权重 60%，PB 权重 40%）
            if pe_percentile is not None and pb_percentile is not None:
                combined_percentile = pe_percentile * 0.6 + pb_percentile * 0.4
            elif pe_percentile is not None:
                combined_percentile = pe_percentile
            elif pb_percentile is not None:
                combined_percentile = pb_percentile
            else:
                combined_percentile = 50  # 默认合理
            
            # PEG 调整
            if peg is not None:
                if peg < 0.5:
                    combined_percentile -= 10  # 严重低估
                elif peg < 1.0:
                    combined_percentile -= 5  # 低估
                elif peg > 2.0:
                    combined_percentile += 10  # 严重高估
                elif peg > 1.5:
                    combined_percentile += 5  # 高估
            
            # 评级映射
            if combined_percentile <= 20:
                return "严重低估"
            elif combined_percentile <= 40:
                return "低估"
            elif combined_percentile <= 60:
                return "合理"
            elif combined_percentile <= 80:
                return "高估"
            else:
                return "严重高估"
                
        except Exception as e:
            logger.error(f"估值评级失败: {e}")
            return "未知"


# 测试代码
if __name__ == '__main__':
    analyzer = ValuationAnalyzer()
    result = analyzer.analyze('000001.SZ')
    
    print("=" * 60)
    print("平安银行 000001.SZ 估值分析")
    print("=" * 60)
    
    print("\n【当前估值】")
    for k, v in result.get('current_valuation', {}).items():
        print(f"  {k}: {v}")
    
    print("\n【历史分位】")
    for k, v in result.get('historical_percentile', {}).items():
        print(f"  {k}: {v}")
    
    print(f"\n【PEG】: {result.get('peg')}")
    
    print("\n【DCF 估值】")
    for k, v in result.get('dcf_valuation', {}).items():
        print(f"  {k}: {v}")
    
    print(f"\n【估值评级】: {result.get('rating')}")
