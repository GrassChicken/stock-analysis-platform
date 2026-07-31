"""
基本面分析引擎

五维度分析：盈利能力、成长性、偿债能力、运营效率、现金流
"""
import logging
import time
from typing import Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv
from app.services.data.tushare_client import get_tushare_client

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self):
        self.pro = get_tushare_client().pro
    
    def _format_code(self, code: str) -> str:
        """格式化股票代码"""
        code = code.strip()
        if '.' in code:
            return code.upper()
        if code.startswith(('6', '9')):
            return f"{code}.SH"
        return f"{code}.SZ"
    
    def _safe_round(self, value, decimals=2):
        """安全的四舍五入，处理 None 和异常值"""
        if value is None or pd.isna(value):
            return None
        try:
            return round(float(value), decimals)
        except:
            return None
    
    def analyze(self, code: str, preloaded: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        五维度基本面分析
        
        Args:
            code: 股票代码（如 000001.SZ 或 000001）
            preloaded: 预加载数据字典（来自 DataCollector），含 fina_df/income_df/balance_df/cashflow_df
        
        Returns:
            分析结果字典
        """
        ts_code = self._format_code(code)
        logger.info(f"开始基本面分析: {ts_code}")
        
        try:
            # 使用预加载数据或自行获取
            if preloaded:
                fina_df = preloaded.get('fina_df', pd.DataFrame())
                income_df = preloaded.get('income_df', pd.DataFrame())
                balance_df = preloaded.get('balance_df', pd.DataFrame())
                cashflow_df = preloaded.get('cashflow_df', pd.DataFrame())
            else:
                # 获取财务指标数据
                time.sleep(0.3)
                fina_df = self.pro.fina_indicator(ts_code=ts_code)
                
                # 获取利润表
                time.sleep(0.3)
                income_df = self.pro.income(ts_code=ts_code)
                
                # 获取资产负债表
                time.sleep(0.3)
                balance_df = self.pro.balancesheet(ts_code=ts_code)
                
                # 获取现金流量表
                time.sleep(0.3)
                cashflow_df = self.pro.cashflow(ts_code=ts_code)
            
            # 五维度分析
            result = {
                'code': ts_code,
                'profitability': self._analyze_profitability(fina_df),
                'growth': self._analyze_growth(fina_df, income_df),
                'solvency': self._analyze_solvency(fina_df, balance_df),
                'efficiency': self._analyze_efficiency(fina_df),
                'cashflow': self._analyze_cashflow(cashflow_df, income_df),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"✓ 基本面分析完成: {ts_code}")
            return result
            
        except Exception as e:
            logger.error(f"基本面分析失败: {ts_code}, {e}")
            return {
                'code': ts_code,
                'error': str(e),
                'profitability': {},
                'growth': {},
                'solvency': {},
                'efficiency': {},
                'cashflow': {}
            }
    
    def _analyze_profitability(self, fina_df: pd.DataFrame) -> Dict[str, Any]:
        """盈利能力分析"""
        if fina_df.empty:
            return {}
        
        try:
            # 取最新一期数据
            latest = fina_df.iloc[0]
            
            return {
                'roe': self._safe_round(latest.get('roe')),
                'roe_trend': self._safe_round(latest.get('roe_waa')),
                'gross_margin': self._safe_round(latest.get('grossprofit_margin')),
                'net_margin': self._safe_round(latest.get('netprofit_margin')),
                'roa': self._safe_round(latest.get('roa')),
                'eps': self._safe_round(latest.get('eps'))
            }
        except Exception as e:
            logger.error(f"盈利能力分析失败: {e}")
            return {}
    
    def _analyze_growth(self, fina_df: pd.DataFrame, income_df: pd.DataFrame) -> Dict[str, Any]:
        """成长性分析"""
        if fina_df.empty:
            return {}
        
        try:
            # 取最近几期数据
            recent = fina_df.head(8)  # 最近2年（8个季度）
            
            # 计算连续增长季度数
            revenue_growth_col = 'tr_yoy'
            profit_growth_col = 'dt_netprofit_yoy'
            
            revenue_growth_count = 0
            profit_growth_count = 0
            
            if revenue_growth_col in recent.columns:
                for val in recent[revenue_growth_col].dropna():
                    if val > 0:
                        revenue_growth_count += 1
                    else:
                        break
            
            if profit_growth_col in recent.columns:
                for val in recent[profit_growth_col].dropna():
                    if val > 0:
                        profit_growth_count += 1
                    else:
                        break
            
            latest = fina_df.iloc[0]
            
            return {
                'revenue_yoy': self._safe_round(latest.get('tr_yoy')),
                'profit_yoy': self._safe_round(latest.get('dt_netprofit_yoy')),
                'operating_profit_yoy': self._safe_round(latest.get('op_yoy')),
                'revenue_continuous_growth_quarters': revenue_growth_count,
                'profit_continuous_growth_quarters': profit_growth_count
            }
        except Exception as e:
            logger.error(f"成长性分析失败: {e}")
            return {}
    
    def _analyze_solvency(self, fina_df: pd.DataFrame, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """偿债能力分析"""
        if fina_df.empty:
            return {}
        
        try:
            latest = fina_df.iloc[0]
            
            return {
                'debt_to_assets': self._safe_round(latest.get('debt_to_assets')),
                'current_ratio': self._safe_round(latest.get('current_ratio')),
                'quick_ratio': self._safe_round(latest.get('quick_ratio'))
            }
        except Exception as e:
            logger.error(f"偿债能力分析失败: {e}")
            return {}
    
    def _analyze_efficiency(self, fina_df: pd.DataFrame) -> Dict[str, Any]:
        """运营效率分析"""
        if fina_df.empty:
            return {}
        
        try:
            latest = fina_df.iloc[0]
            
            return {
                'assets_turn': self._safe_round(latest.get('assets_turn')),
                'receivables_turn': self._safe_round(latest.get('ar_turn')),
                'inventory_turn': self._safe_round(latest.get('inv_turn')),
                'fixed_assets_ratio': self._safe_round(latest.get('fix_ass_ratio'))
            }
        except Exception as e:
            logger.error(f"运营效率分析失败: {e}")
            return {}
    
    def _analyze_cashflow(self, cashflow_df: pd.DataFrame, income_df: pd.DataFrame) -> Dict[str, Any]:
        """现金流分析"""
        if cashflow_df.empty or income_df.empty:
            return {}
        
        try:
            # 取最新一期
            latest_cash = cashflow_df.iloc[0]
            latest_income = income_df.iloc[0]
            
            # 经营现金流
            operating_cashflow = latest_cash.get('n_cashflow_act')
            
            # 净利润
            net_profit = latest_income.get('n_income_attr_p')
            
            # 自由现金流（经营现金流 - 资本支出）
            invest_cashflow = latest_cash.get('n_cashflow_inv_act')
            free_cashflow = None
            if operating_cashflow and invest_cashflow:
                free_cashflow = operating_cashflow + invest_cashflow  # 投资现金流通常是负数
            
            # 现金流覆盖率
            cashflow_coverage = None
            if operating_cashflow and net_profit and net_profit > 0:
                cashflow_coverage = (operating_cashflow / net_profit) * 100
            
            return {
                'operating_cashflow': self._safe_round(operating_cashflow / 10000),  # 转换为万元
                'free_cashflow': self._safe_round(free_cashflow / 10000) if free_cashflow else None,
                'cashflow_coverage': self._safe_round(cashflow_coverage),
                'invest_cashflow': self._safe_round(invest_cashflow / 10000) if invest_cashflow else None
            }
        except Exception as e:
            logger.error(f"现金流分析失败: {e}")
            return {}


# 测试代码
if __name__ == '__main__':
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze('000001.SZ')
    
    print("=" * 60)
    print("平安银行 000001.SZ 基本面分析")
    print("=" * 60)
    
    print("\n【盈利能力】")
    for k, v in result.get('profitability', {}).items():
        print(f"  {k}: {v}")
    
    print("\n【成长性】")
    for k, v in result.get('growth', {}).items():
        print(f"  {k}: {v}")
    
    print("\n【偿债能力】")
    for k, v in result.get('solvency', {}).items():
        print(f"  {k}: {v}")
    
    print("\n【运营效率】")
    for k, v in result.get('efficiency', {}).items():
        print(f"  {k}: {v}")
    
    print("\n【现金流】")
    for k, v in result.get('cashflow', {}).items():
        print(f"  {k}: {v}")
